"""Base command line helpers for analyzers."""

import datetime
import json
import logging
import platform
import sys
import typing

import click
import distro
import requests

_LOG = logging.getLogger(__name__)


def _get_click_arguments(click_ctx: click.core.Command) -> dict:
    """Get arguments supplied to analyzer."""
    arguments = {}

    ctx = click_ctx
    while ctx:
        assert ctx.info_name not in arguments, "Analyzers cannot use nested sub-commands with same name"
        assert not ctx.args, "Analyzer cannot accept positional arguments, all arguments should be named"

        arguments[ctx.info_name] = dict(ctx.params)
        ctx = ctx.parent

    return arguments


def print_command_result(click_ctx: click.core.Command, result: typing.Union[dict, list],
                         analyzer: str, analyzer_version: str, output: str = None, pretty: bool = True) -> None:
    """Print or submit results, nicely if requested."""
    metadata = {
        'analyzer': analyzer,
        'datetime': datetime.datetime.now().isoformat(),
        'hostname': platform.node(),
        'version': analyzer_version,
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
        _LOG.info("Successfully submitted results to remote, response: %s", response.json())
        return

    kwargs = {}
    if pretty:
        kwargs['sort_keys'] = True
        kwargs['separators'] = (',', ': ')
        kwargs['indent'] = 2

    content = json.dumps(content, **kwargs)
    if output is None or output == '-':
        sys.stdout.write(content)
    else:
        _LOG.info("Writing results to %r", output)
        with open(output, 'w') as output_file:
            output_file.write(content)
