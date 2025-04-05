"""
Module for importing and processing PTM files with environment variable support.
"""

import os
import sys
import inspect
from importlib.util import spec_from_file_location
from typing import Tuple, Optional

from .logger import plog
from .loader import PTMLoader
from .param import Parameter

def _get_parent_parameter():
    caller_frame = inspect.stack()
    caller_frame = caller_frame[2].frame
    return caller_frame.f_globals.get("param", None)

def _abs_include_path(file_path: str) -> str:
    """
    Resolve the absolute path of a file.
    
    Args:
        file_path: The path to resolve (can be absolute or relative)
        
    Returns:
        The absolute path to the file
    """
    if os.path.isabs(file_path):
        return file_path
    else:
        caller_frame = inspect.stack()
        caller_file = caller_frame[2].filename

        if caller_file.endswith(".ptm"):
            caller_dir = os.path.dirname(os.path.abspath(caller_file))
            abs_path = os.path.abspath(os.path.join(caller_dir, file_path))
        else:
            abs_path = os.path.abspath(file_path)

        return abs_path


def include(file_path: str, param: Optional[Parameter] = None) -> str:
    """
    Import a PTM file and process environment variables during import.
    
    This function enables importing .ptm files with environment variable support.
    It creates a new module and executes it with the PTMLoader.
    
    Args:
        file_path: Path to the PTM file to import (can be absolute or relative)
        
    Returns:
        str: The generated unique module name
    """
    if not file_path.endswith(".ptm"):
        raise ValueError("Can only import .ptm files")

    # Resolve the path relative to the caller's directory
    file_real_path = _abs_include_path(file_path)

    if not os.path.exists(file_real_path):
        raise FileNotFoundError(f"File does not exist: {file_real_path}")
    
    module_name = file_real_path
    plog.info(f"Loading PTM file {file_real_path}")

    spec = spec_from_file_location(
        module_name, file_real_path, loader=PTMLoader(module_name, file_real_path)
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create module spec: {file_real_path}")

    # Create new module
    module = sys.modules.get(module_name)
    if module is None:
        module = type(sys)(module_name)
        sys.modules[module_name] = module

    # Set basic module attributes
    module.__file__ = file_real_path
    module.__name__ = module_name
    module.__package__ = None
    module.__spec__ = spec
    module.__loader__ = spec.loader

    # Add utility functions to the module
    module.include = include
    module.ptm = sys.modules["ptm"]

    if param is None:
        param = _get_parent_parameter()
    module.param = param
    
    # Execute module
    spec.loader.exec_module(module)

    return module
