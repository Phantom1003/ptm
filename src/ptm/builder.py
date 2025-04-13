from typing import List, Dict, Callable, Any, Optional, Set, Union
from functools import wraps
from collections import defaultdict
import functools
from pathlib import Path
import time
import os

from .logger import plog

class BuildTarget:
    def __init__(self, recipe: Callable, target: str, depends: List[str]):
        self.target = target
        self.depends = depends
        self.recipe = recipe
        self.timestamp = self._get_timestamp(self.target)

    def _get_timestamp(self, path: str) -> int:
        if os.path.exists(path):
            return os.stat(path).st_mtime_ns
        else:
            return 0

    def _invalid(self) -> bool:
        if self.timestamp == 0:
            return True

        for depend in self.depends:
            if self._get_timestamp(depend) >= self.timestamp:
                return True

        return False   

    def build(self, **kwargs) -> Any:
        if not self._invalid():
            plog.info(f"Target '{self.target}' is up to date")

        else:
            plog.info(f"Building target: {self.target}")
            if os.path.isabs(self.target):
                os.makedirs(os.path.dirname(self.target), exist_ok=True)

            self.recipe(**kwargs)
            self.timestamp = self._get_timestamp(self.target)

class BuildSystem:
    _instance = None
    
    def __init__(self):
        if BuildSystem._instance is not None:
            raise RuntimeError("BuildSystem is a singleton")
            
        self.target_lut: Dict[str, BuildTarget] = {}
        self._visited: Dict[str, bool] = {}
        self._build_order: List[str] = []
        
    @classmethod
    def get_instance(cls) -> 'BuildSystem':
        if cls._instance is None:
            cls._instance = BuildSystem()
        return cls._instance

    def _register_target(self, func: Callable, target: Union[str, Callable], depends: List[Union[str, Callable]]) -> Callable:
        gen_real_target = lambda target_name: target_name.__name__ if isinstance(target_name, Callable) else os.path.abspath(target_name)
        target_real_name = gen_real_target(target)
        depends_real_name = [gen_real_target(depend) for depend in depends]

        partial_func = functools.partial(func, target_real_name, depends_real_name)
        partial_func.__name__ = func.__name__
        build_target = BuildTarget(partial_func, target_real_name, depends_real_name)
        self.target_lut[target_real_name] = build_target
        return func

    def targets(self, targets: List[Union[str, Callable]], depends: List[Union[str, Callable]] = []):           
        def decorator(func):
            for target in targets:
                self._register_target(func, target, depends)
            return func
        return decorator

    def target(self, target: Union[str, Callable], depends: List[Union[str, Callable]] = []):           
        def decorator(func):
            return self._register_target(func, target, depends)
        return decorator

    def task(self, depends: List[Union[str, Callable]] = []):
        def decorator(func):
            return self._register_target(func, func, depends)
        return decorator

    def get_target(self, name: str) -> Optional[BuildTarget]:
        return self.target_lut.get(name)

    def _visit(self, target: str) -> None:
        if target not in self.target_lut:
            return

        if self._visited.get(target, False):
            raise ValueError(f"Circular dependency detected involving target: {target}")
        self._visited[target] = True

        for dep in self.target_lut[target].depends:
            self._visit(dep)

        self._build_order.append(target)

    def get_build_order(self, target: str) -> List[str]:
        self._visited.clear()
        self._build_order.clear()
        
        self._visit(target)
        return self._build_order

    def build(self, target: Union[str, Callable]) -> Any:
        if isinstance(target, Callable):
            target = target.__name__
        else:
            target = os.path.abspath(target)

        if target not in self.target_lut:
            raise ValueError(f"Target '{target}' not found")
            
        build_order = self.get_build_order(target)
        results = {}
        
        for t in build_order:
            if t in self.target_lut:
                results[t] = self.target_lut[t].build()
                
        return results[target]

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
