"""
Module for executing shell commands.
"""

import subprocess
from typing import Optional, Tuple, Union

from .logger import plog


def exec(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> int:
    """
    Execute a shell command and return its exit status.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        int: The exit status of the command
    """
    plog.info(cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    process.communicate()
    return process.returncode


def exec_stdout(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command and return its standard output.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        str: The standard output of the command
    """
    plog.info(cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, _ = process.communicate()
    return stdout.strip()


def exec_stderr(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command and return its standard error.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        str: The standard error of the command
    """
    plog.info(cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    _, stderr = process.communicate()
    return stderr.strip()


def exec_stdout_stderr(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command and return combined standard output and error.
    
    Args:
        cmd: The command to execute
        shell: Whether to use shell execution
        cwd: Working directory for the command
        
    Returns:
        str: The combined standard output and error of the command
    """
    plog.info(cmd)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return (stdout + stderr).strip() 