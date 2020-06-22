#!/usr/bin/env python3
# thoth-analyzer
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

import datetime
import json
import logging
import os
import platform
import sys
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import click
import distro
import requests

from thoth.common import SafeJSONEncoder
from thoth.common import datetime2datetime_str

_LOG = logging.getLogger(__name__)
_ETC_OS_RELEASE = "/etc/os-release"


def _get_click_arguments(click_ctx: click.Context) -> Dict[Optional[str], Any]:
    """Get arguments supplied to analyzer."""
    arguments: Dict[Optional[str], Any] = {}
    ctx: Optional[click.Context] = click_ctx
    while ctx:
        # Ignore PycodestyleBear (E501)
        assert ctx.info_name not in arguments, "Analyzers cannot use nested sub-commands with same name"
        # Ignore PycodestyleBear (E501)
        assert not ctx.args, "Analyzer cannot accept positional arguments, all arguments should be named"

        report = {}
        for key, value in dict(ctx.params).items():
            # If the given argument was provided as a JSON, parse it so we have structured reports.
            try:
                parsed_value = json.loads(value)
                if isinstance(parsed_value, dict):
                    value = parsed_value
            except Exception:
                pass
            report[key] = value

        arguments[ctx.info_name] = report

        ctx = ctx.parent

    return arguments


def _gather_os_release() -> Optional[Dict[str, str]]:
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

    return result


def print_command_result(
    click_ctx: click.Context,
    result: Union[Dict[str, Any], List[Any]],
    analyzer: str,
    analyzer_version: str,
    output: Optional[str] = None,
    duration: Optional[float] = None,
    pretty: bool = True,
    dry_run: bool = False
) -> None:
    """Print or submit results, nicely if requested."""
    metadata = {
        'analyzer': analyzer,
        'datetime': datetime2datetime_str(datetime.datetime.utcnow()),
        'timestamp': int(time.time()),
        'hostname': platform.node(),
        'analyzer_version': analyzer_version,
        'distribution': distro.info(),
        'arguments': _get_click_arguments(click_ctx),
        'duration': int(duration) if duration is not None else None,
        'python': {
            'major': sys.version_info.major,
            'minor': sys.version_info.minor,
            'micro': sys.version_info.micro,
            'releaselevel': sys.version_info.releaselevel,
            'serial': sys.version_info.serial,
            'api_version': sys.api_version,
            'implementation_name': sys.implementation.name
        }
    }

    content = {
        'result': result,
        'metadata': metadata
    }

    if dry_run:
        _LOG.info("Printing results to log")
        _LOG.info(content)
        return

    if isinstance(output, str) and output.startswith(('http://', 'https://')):
        _LOG.info("Submitting results to %r", output)
        response = requests.post(output, json=content)
        response.raise_for_status()
        _LOG.info(
            "Successfully submitted results to %r, response: %s",
            output,
            response.json()
        )
        return

    kwargs = {
        'cls': SafeJSONEncoder,
    }
    if pretty:
        kwargs['sort_keys'] = True
        kwargs['separators'] = (',', ': ')
        kwargs['indent'] = 2

    serialized_content = json.dumps(content, **kwargs)
    if output is None or output == '-':
        sys.stdout.write(serialized_content)
    else:
        _LOG.info("Writing results to %r", output)
        with open(output, 'w') as output_file:
            output_file.write(serialized_content)
