"""Shared code logic in Thoth analyzers."""

from .cli import print_command_result
from .command import CommandError
from .command import CommandResult
from .command import run_command

from thoth.common import __version__ as __common__version__

__title__ = 'thoth-analyzer'
__version__ = f"0.1.0+common.{__common__version__}"
