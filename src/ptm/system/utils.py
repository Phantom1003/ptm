import os
from typing import List, Union, Callable

def _get_target_name(target: Union[str, Callable]) -> str:
    return target.__name__ if callable(target) else os.path.abspath(target)

def _get_timestamp(path: str) -> int:
    if os.path.exists(path):
        return os.stat(path).st_mtime_ns
    else:
        return 0

def _get_depends(target: Union[str, Callable], depends: Union[List[Union[str, Callable]], Callable]) -> List[Union[str, Callable]]:
    if callable(target):
        target = target.__name__

    if callable(depends):
        return depends(target)
    else:
        return depends

