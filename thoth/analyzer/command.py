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

"""Handling invoking commands of external programs in a sane way."""

import json
import logging

import delegator

_LOG = logging.getLogger(__name__)


class CommandResult(object):
    """Representation of result of a command invocation."""

    def __init__(self, command: delegator.Command, is_json: bool = False):
        """Initialiaztion of a command result wrapper for delegator."""
        self.command = command
        self.is_json = is_json
        self._stdout = None

    @property
    def stdout(self):
        """Standard output from invocation."""
        if self._stdout is None:
            if self.is_json:
                self._stdout = json.loads(self.command.out)
            else:
                self._stdout = self.command.out

        return self._stdout

    @property
    def stderr(self):
        """Standard error output from invocation."""
        return self.command.err

    @property
    def return_code(self):
        """Process return code."""
        return self.command.return_code

    @property
    def timeout(self):
        """Timeout that was given to the invoked process to finish."""
        return self.command.timeout

    def to_dict(self):
        """Represent command result as a dict."""
        return {
            'stdout': self.stdout,
            'stderr': self.stderr,
            'return_code': self.return_code,
            'command': self.command.cmd,
            'timeout': self.timeout,
            'message': str(self)
        }


class CommandError(RuntimeError, CommandResult):
    """Exception raised on error when calling commands.

    Note that this class inherits also from CommandResult, so you can directly
    access to_dict() or other defined methods.
    """

    def __init__(self, *args, command: delegator.Command,
                 **command_result_kwargs):
        """Store information about command error."""
        RuntimeError.__init__(self, *args)
        CommandResult.__init__(self, command=command,
                               **command_result_kwargs)

    @property
    def stdout(self):
        """Standard output from invocation.

        Override implementation for errors, not all tools product JSON or
        errors so try to avoid parsing JSON implicitly.
        """
        return self.command.out


def run_command(cmd, timeout=60, is_json=False, env=None, raise_on_error=True):
    """Run the given command, block until it finishes."""
    _LOG.debug("Running command %r", cmd)
    command = delegator.run(cmd, block=True, timeout=timeout, env=env)

    if command.return_code != 0 and raise_on_error:
        error_msg = "Command exited with non-zero status code ({}): {}".format(
            command.return_code, command.err)
        _LOG.debug(error_msg)
        raise CommandError(error_msg, command=command, is_json=is_json)

    return CommandResult(command, is_json=is_json)
