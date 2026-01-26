from .version import __version__
from .cli import main as cli_main
from .syntax.param import Parameter
from .syntax.arglist import ArgList
from .syntax.include import include
from .syntax.environ import environ
from .syntax.shell import exec_cmd, exec_cmd_stdout, exec_cmd_stderr, exec_cmd_stdout_stderr
from .system.builder import builder, task, target, template
from .system.project import Project

__all__ = [
    "task", "target", "template", "builder",
    "Parameter", "ArgList",
    "include",
    "environ",
    "exec_cmd", "exec_cmd_stdout", "exec_cmd_stderr", "exec_cmd_stdout_stderr",
    "Project",
    "__version__",
]

def main():
    cli_main()
