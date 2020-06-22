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

"""Handling invoking commands of external programs in a sane way."""

import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import delegator

_LOG = logging.getLogger(__name__)


class CommandResult:
    """Representation of result of a command invocation."""

    def __init__(self, command: delegator.Command, is_json: bool = False):
        """Initialization of a command result wrapper for delegator."""
        self.command = command
        self.is_json = is_json
        self._stdout: Optional[Union[Dict[Any, Any], str]] = None

    @property
    def stdout(self) -> Optional[Union[str, Dict[Any, Any]]]:
        """Standard output from invocation."""
        if self._stdout is None:
            if self.is_json:
                self._stdout = json.loads(self.command.out)
            else:
                self._stdout = self.command.out

        return self._stdout

    @property
    def stderr(self) -> str:
        """Standard error output from invocation."""
        return self.command.err  # type: ignore

    @property
    def return_code(self) -> int:
        """Process return code."""
        return self.command.return_code  # type: ignore

    @property
    def timeout(self) -> int:
        """Timeout that was given to the invoked process to finish."""
        return self.command.timeout  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
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

    def __init__(
        self,
        *args: Any,
        command: delegator.Command,
        **command_result_kwargs: Any
    ) -> None:
        """Store information about command error."""
        RuntimeError.__init__(self, *args)
        CommandResult.__init__(self, command=command,
                               **command_result_kwargs)

    @property
    def stdout(self) -> Union[str, Dict[str, Any]]:
        """Standard output from invocation.

        Override implementation for errors, not all tools product JSON or
        errors so try to avoid parsing JSON implicitly.
        """
        return self.command.out  # type: ignore


def run_command(
    cmd: Union[List[str], str],
    timeout: int = 60,
    is_json: bool = False,
    env: Optional[Dict[str, str]] = None,
    raise_on_error: bool = True
) -> CommandResult:
    """Run the given command, block until it finishes."""
    _LOG.debug("Running command %r", cmd)
    command = delegator.run(cmd, block=True, timeout=timeout, env=env)

    if command.return_code != 0 and raise_on_error:
        error_msg = "Command exited with non-zero status code ({}): {}".format(
            command.return_code, command.err)
        _LOG.debug(error_msg)
        raise CommandError(error_msg, command=command, is_json=is_json)

    return CommandResult(command, is_json=is_json)
