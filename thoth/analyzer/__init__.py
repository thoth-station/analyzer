"""Shared code logic in Thoth analyzers."""

__title__ = 'thoth-analyzer'
__version__ = '0.0.5'

from .cli import print_command_result
from .command import CommandError
from .command import CommandResult
from .command import run_command
