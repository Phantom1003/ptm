import os
import sys
import inspect
from importlib.util import spec_from_file_location

from .logger import plog
from .loader import PTMLoader


def _include_relocate_path(file_path: str) -> tuple[str, str]:
    if os.path.isabs(file_path):
        return file_path, os.path.splitext(os.path.basename(file_path))[0]
    else:
        caller_frame = inspect.stack()
        caller_file = caller_frame[2].filename

        if caller_file.endswith(".ptm"):
            caller_dir = os.path.dirname(os.path.abspath(caller_file))
            abs_path = os.path.abspath(os.path.join(caller_dir, file_path))
        else:
            abs_path = os.path.abspath(file_path)

        return abs_path, os.path.splitext(os.path.basename(file_path))[0]


def include(file_path: str) -> str:
    """
    Import a PTM file and process environment variables during import

    Args:
        file_path: Path to the PTM file to import (can be absolute or relative)

    Returns:
        str: The generated unique module name
    """
    if not file_path.endswith(".ptm"):
        raise ValueError("Can only import .ptm files")

    # Resolve the path relative to the caller's directory
    file_real_path, file_basename = _include_relocate_path(file_path)

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

    module.include = include
    module.os = os

    # Execute module
    spec.loader.exec_module(module)

    return module
