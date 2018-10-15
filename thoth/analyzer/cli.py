#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# thoth-analyzer
# Copyright(C) 2018 Fridolin Pokorny
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


def _get_click_arguments(click_ctx: click.core.Command) -> dict:
    """Get arguments supplied to analyzer."""
    arguments = {}

    ctx = click_ctx
    while ctx:
        # Ignore PycodestyleBear (E501)
        assert ctx.info_name not in arguments, "Analyzers cannot use nested sub-commands with same name"
        # Ignore PycodestyleBear (E501)
        assert not ctx.args, "Analyzer cannot accept positional arguments, all arguments should be named"

        arguments[ctx.info_name] = dict(ctx.params)
        ctx = ctx.parent

    return arguments


def print_command_result(click_ctx: click.core.Command,
                         result: typing.Union[dict, list], analyzer: str,
                         analyzer_version: str, output: str = None,
                         pretty: bool = True) -> None:
    """Print or submit results, nicely if requested."""
    metadata = {
        'analyzer': analyzer,
        'datetime': datetime2datetime_str(datetime.datetime.utcnow()),
        'timestamp': int(time.time()),
        'hostname': platform.node(),
        'analyzer_version': analyzer_version,
        'distribution': distro.info(),
        'arguments': _get_click_arguments(click_ctx),
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

    if isinstance(output, str) and output.startswith(('http://', 'https://')):
        _LOG.info("Submitting results to %r", output)
        response = requests.post(output, json=content)
        response.raise_for_status()
        _LOG.info(
            "Successfully submitted results to remote, response: %s", response.json())  # Ignore PycodestyleBear (E501)
        return

    kwargs = {}
    if pretty:
        kwargs['sort_keys'] = True
        kwargs['separators'] = (',', ': ')
        kwargs['indent'] = 2

    content = json.dumps(content, **kwargs, cls=SafeJSONEncoder)
    if output is None or output == '-':
        sys.stdout.write(content)
    else:
        _LOG.info("Writing results to %r", output)
        with open(output, 'w') as output_file:
            output_file.write(content)
