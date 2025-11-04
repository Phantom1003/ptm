"""
Module for executing shell commands.
"""

import subprocess
from typing import Optional
import shlex

from ..system.logger import plog


def _check_return_code(returncode: int) -> None:
    """
    Check the return code of a subprocess and raise an exception if it's non-zero.
    
    Args:
        returncode: The return code of the subprocess
    """
    if returncode != 0:
        raise RuntimeError(f"Command failed with return code {returncode}")

def exec_cmd(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> int:
    """
    Execute a shell command and return its exit status.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command

    Returns:
        int: The exit status of the command
    """
    plog.debug("Executing command:", cmd)
    cmd = " ".join(shlex.split(cmd))
    plog.info(cmd)

    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=None,
        stderr=None,
        text=True
    )
    process.communicate()
    _check_return_code(process.returncode)

    return process.returncode


def exec_cmd_stdout(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command and return its standard output.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        str: The standard output of the command
    """
    plog.debug(cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, _ = process.communicate()
    _check_return_code(process.returncode)

    return stdout.strip()


def exec_cmd_stderr(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command and return its standard error.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        str: The standard error of the command
    """
    plog.debug("Executing command:", cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    _, stderr = process.communicate()
    _check_return_code(process.returncode)

    return stderr.strip()


def exec_cmd_stdout_stderr(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command and return combined standard output and error.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        str: The combined standard output and error of the command
    """
    plog.debug("Executing command:", cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    _check_return_code(process.returncode)

    return (stdout + stderr).strip()
