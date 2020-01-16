#!/usr/bin/env python3
# thoth-analyzer
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Base command line helpers for analyzers."""

import os
import datetime
import json
import logging
import platform
import sys
import time
import typing

import click
import distro
import requests

from thoth.common import SafeJSONEncoder
from thoth.common import datetime2datetime_str

_LOG = logging.getLogger(__name__)
_ETC_OS_RELEASE = "/etc/os-release"
_OS_RELEASE_KEYS = frozenset(
    (
        "id",
        "name",
        "platform_id",
        "redhat_bugzilla_product",
        "redhat_bugzilla_product_version",
        "redhat_support_product",
        "redhat_support_product_version",
        "variant_id",
        "version",
        "version_id",
    )
)


def _get_click_arguments(click_ctx: click.core.Command) -> dict:
    """Get arguments supplied to analyzer."""
    arguments = {}

    ctx = click_ctx
    while ctx:
        # Ignore PycodestyleBear (E501)
        assert (
            ctx.info_name not in arguments
        ), "Analyzers cannot use nested sub-commands with same name"
        # Ignore PycodestyleBear (E501)
        assert (
            not ctx.args
        ), "Analyzer cannot accept positional arguments, all arguments should be named"

        report = {}
        for key, value in dict(ctx.params).items():
            # If the given argument was provided as a JSON, parse it so we have structured reports.
            try:
                parsed_value = json.loads(value)
                if isinstance(parsed_value, (dict, list)) or parsed_value is None:
                    value = parsed_value
            except Exception:
                pass
            report[key] = value

        arguments[ctx.info_name] = report

        ctx = ctx.parent

    return arguments


def _gather_os_release():
    """Gather information about operating system used."""
    if not os.path.isfile(_ETC_OS_RELEASE):
        return None

    try:
        with open(_ETC_OS_RELEASE, "r") as os_release_file:
            content = os_release_file.read()
    except Exception:
        return None

    result = {}
    for line in content.splitlines():
        parts = line.split("=", maxsplit=1)
        if len(parts) != 2:
            continue

        key = parts[0].lower()
        value = parts[1].strip('"')

        result[key] = value

    # Filter out some of the entries, keep just the most important ones.
    return {k: v for k, v in result.items() if k in _OS_RELEASE_KEYS}


def print_command_result(
    click_ctx: click.core.Command,
    result: typing.Union[dict, list],
    analyzer: str,
    analyzer_version: str,
    output: str = None,
    duration: float = None,
    pretty: bool = True,
    dry_run: bool = False,
) -> None:
    """Print or submit results, nicely if requested."""
    metadata = {
        "analyzer": analyzer,
        "datetime": datetime2datetime_str(datetime.datetime.utcnow()),
        "document_id": os.getenv("THOTH_DOCUMENT_ID"),
        "timestamp": int(time.time()),
        "hostname": platform.node(),
        "analyzer_version": analyzer_version,
        "distribution": distro.info(),
        "arguments": _get_click_arguments(click_ctx),
        "duration": int(duration) if duration is not None else None,
        "python": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
            "releaselevel": sys.version_info.releaselevel,
            "serial": sys.version_info.serial,
            "api_version": sys.api_version,
            "implementation_name": sys.implementation.name,
        },
        "os_release": _gather_os_release(),
        "thoth_deployment_name": os.getenv("THOTH_DEPLOYMENT_NAME"),
    }

    content = {"result": result, "metadata": metadata}

    if dry_run:
        _LOG.info("Printing results to log")
        _LOG.info(content)
        return

    if isinstance(output, str) and output.startswith(("http://", "https://")):
        _LOG.info("Submitting results to %r", output)
        response = requests.post(output, json=content)
        response.raise_for_status()
        _LOG.info(
            "Successfully submitted results to %r, response: %s",
            output,
            response.json(),
        )  # Ignore PycodestyleBear (E501)
        return

    kwargs = {}
    if pretty:
        kwargs["sort_keys"] = True
        kwargs["separators"] = (",", ": ")
        kwargs["indent"] = 2

    content = json.dumps(content, **kwargs, cls=SafeJSONEncoder)
    if output is None or output == "-":
        sys.stdout.write(content)
    else:
        _LOG.info("Writing results to %r", output)
        with open(output, "w") as output_file:
            output_file.write(content)
