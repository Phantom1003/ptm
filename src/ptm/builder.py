import os
import functools
from typing import List, Dict, Callable, Any, Optional, Union
from collections import defaultdict

from .logger import plog
from .recipe import BuildRecipe, DependencyTree
from .scheduler import BuildScheduler

def _get_target_name(target: Union[str, Callable]) -> str:
    return target.__name__ if callable(target) else os.path.abspath(target)

def _get_depends(target: Union[str, Callable], depends: Union[List[Union[str, Callable]], Callable]) -> List[Union[str, Callable]]:
    if callable(target):
        target = target.__name__

    if callable(depends):
        return depends(target)
    else:
        return depends

class BuildSystem:
    _instance = None
    
    def __init__(self):
        if BuildSystem._instance is not None:
            raise RuntimeError("BuildSystem is a singleton")
            
        self.target_lut: Dict[str, BuildRecipe] = {}
        self.default_max_jobs: int = os.cpu_count() or 1

    @classmethod
    def get_instance(cls) -> 'BuildSystem':
        if cls._instance is None:
            cls._instance = BuildSystem()
        return cls._instance

    def _register_target(self, func: Callable, target: Union[str, Callable], depends: List[Union[str, Callable]], external: bool = False) -> Callable:
        target_real_name = _get_target_name(target)
        depends_real_name = [_get_target_name(depend) for depend in depends]

        func_sig_args = func.__code__.co_varnames
        if func_sig_args[0] != 'target' or func_sig_args[1] != 'depends':
            raise ValueError("Task parameters must start with 'target' and 'depends'")

        if external and (len(func_sig_args) < 3 or func_sig_args[2] != 'jobs'):
            raise ValueError("If external is specified, task must accept 'jobs' parameter")

        partial_func = functools.partial(func, target=target_real_name, depends=depends_real_name)
        partial_func.__name__ = func.__name__
        build_target = BuildRecipe(partial_func, target_real_name, depends_real_name, external=bool(external))
        self.target_lut[target_real_name] = build_target
        return func

    def targets(self, targets: List[Union[str, Callable]], depends: Union[List[Union[str, Callable]], Callable] = [], external: bool = None):
        def decorator(func):
            for target in targets:
                self._register_target(func, target, _get_depends(target, depends), external)
            return func
        return decorator

    def target(self, target: Union[str, Callable], depends: Union[List[Union[str, Callable]], Callable] = [], external: bool = None):
        def decorator(func):
            return self._register_target(func, target, _get_depends(target, depends), external)
        return decorator

    def task(self, depends: Union[List[Union[str, Callable]], Callable] = [], external: bool = None):
        def decorator(func):
            return self._register_target(func, func, _get_depends(func, depends), external)
        return decorator

    def build(self, target: Union[str, Callable], *, max_jobs: Optional[int] = None) -> int:
        """Build the target and its dependencies.
        
        Args:
            target: Target name or callable to build
            max_jobs: Maximum number of parallel jobs
        
        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        if max_jobs is not None and max_jobs < 1:
            raise ValueError("Job count must be at least 1!")
        max_jobs = self.default_max_jobs if max_jobs is None else max_jobs

        target = _get_target_name(target)

        if target not in self.target_lut:
            raise ValueError(f"Target '{target}' not found")
        
        tree = DependencyTree(target, self.target_lut)
        scheduler = BuildScheduler(tree.get_build_order(), max_jobs)
        exitcode = scheduler.run()
        return exitcode
    
    def add_dependency(self, target: Union[str, Callable], depends: List[Union[str, Callable]]) -> None:
        target_real_name = _get_target_name(target)
        depends_real_name = [_get_target_name(depend) for depend in depends]

        if target_real_name not in self.target_lut:
            raise ValueError(f"Target '{target_real_name}' not found")

        self.target_lut[target_real_name].depends.extend(depends_real_name)

    def list_targets(self) -> None:
        """List all available targets and their descriptions."""
        plog.info("Available targets:")
        for _, target in self.target_lut.items():
            target_file = f" -> {str(target.target)}" if target.target else ""
            dep_files = f" <- {[str(f) for f in target.depends]}" if target.depends else ""
            plog.info(f"{target_file}: {dep_files}")

# Create global instance and decorator
builder = BuildSystem.get_instance()
task = builder.task
target = builder.target
targets = builder.targets
