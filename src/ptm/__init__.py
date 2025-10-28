from .cli import main as cli_main
from .syntax.param import Parameter
from .syntax.include import include
from .syntax.environ import environ
from .syntax.strdiv import enable_str_truediv
from .syntax.shell import exec_cmd, exec_cmd_stdout, exec_cmd_stderr, exec_cmd_stdout_stderr
from .system.builder import builder, task, target, targets


__all__ = [
    "task", "target", "targets", "builder",
    "Parameter",
    "include",
    "environ",
    "exec_cmd", "exec_cmd_stdout", "exec_cmd_stderr", "exec_cmd_stdout_stderr",
]

enable_str_truediv()

def main():
    cli_main()
