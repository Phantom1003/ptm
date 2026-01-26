import os
import functools
from typing import List, Dict, Callable, Optional, Union

from ..system.logger import plog
from .scheduler import BuildScheduler
from .recipe import BuildTargetType, BuildTarget, BuildRecipe, DependencyTree


class BuildSystem:
    _instance = None
    
    def __init__(self):
        if BuildSystem._instance is not None:
            raise RuntimeError("BuildSystem is a singleton")
            
        self.recipe_lut: Dict[BuildTarget, BuildRecipe] = {}
        self.default_max_jobs: int = os.cpu_count() or 1
        self.ptm_srcs: set[str] = set()

    @classmethod
    def get_instance(cls) -> 'BuildSystem':
        if cls._instance is None:
            cls._instance = BuildSystem()
        return cls._instance
    
    def _get_depends(self, target: Union[str, Callable], depends: Union[List[Union[str, Callable]], Callable]) -> List[Union[str, Callable]]:
        if callable(target):
            target = target.__name__

        if callable(depends):
            return depends(target)
        else:
            return depends

    def _register_target(self, func: Callable, target: Union[str, Callable], depends: List[Union[str, Callable]], external: bool = False) -> Callable:
        build_target = BuildTarget(target)
        build_depends = [BuildTarget(dep) for dep in depends]

        func_sig_args = func.__code__.co_varnames
        if func_sig_args[0] != 'target' or func_sig_args[1] != 'depends':
            raise ValueError("Task parameters must start with 'target' and 'depends'")

        if external and (len(func_sig_args) < 3 or func_sig_args[2] != 'jobs'):
            raise ValueError("If external is specified, task must accept 'jobs' parameter")

        # Pass the display name to the partial function
        target_name = build_target.name
        depends_names = [dep.name if dep.type == BuildTargetType.TASK else dep.uid for dep in build_depends]
        plog.debug(f"Registering target '{target_name}' with depends {depends_names} (external={external})")

        partial_func = functools.partial(func, target=target_name, depends=depends_names)
        partial_func.__name__ = func.__name__
        build_recipe = BuildRecipe(partial_func, build_target, build_depends, external=bool(external))
        self.recipe_lut[build_target] = build_recipe
        return func

    def template(self, targets: List[Union[str, Callable]], depends: Union[List[Union[str, Callable]], Callable] = [], external: bool = False):
        def decorator(func):
            for target in targets:
                self._register_target(func, target, self._get_depends(target, depends), external)
            return func
        return decorator

    def target(self, target: Union[str, Callable, List[str | Callable]], depends: Union[List[Union[str, Callable]], Callable] = [], external: bool = False):
        def decorator(func):
            if isinstance(target, list):
                first_t = target[0]
                self._register_target(func, first_t, self._get_depends(first_t, depends), external)

                if len(target) > 1:
                    def dummy_task(target, depends):
                        return
                    for t in target[1:]:
                        self._register_target(dummy_task, t, [first_t])
                return func
            else:
                return self._register_target(func, target, self._get_depends(target, depends), external)
        return decorator

    def task(self, depends: Union[List[Union[str, Callable]], Callable] = [], external: bool = False):
        def decorator(func):
            return self._register_target(func, func, self._get_depends(func, depends), external)
        return decorator

    def generate_dependency_tree(self, target: Union[str, Callable, BuildTarget]) -> DependencyTree:
        return DependencyTree(target, self.recipe_lut)

    def build(self, target: Union[str, Callable, BuildTarget], max_jobs: int = 1) -> int:
        tree = self.generate_dependency_tree(target)
        scheduler = BuildScheduler(tree.generate_build_order(), max_jobs)
        exitcode = scheduler.run()
        return exitcode
    
    def add_dependency(self, target: Union[str, Callable], depends: List[Union[str, Callable]]) -> None:
        build_target = BuildTarget(target)
        build_depends = [BuildTarget(dep) for dep in depends]

        if build_target not in self.recipe_lut:
            raise ValueError(f"Target '{build_target}' not found")

        self.recipe_lut[build_target].depends.extend(build_depends)

    def list_targets(self) -> None:
        plog.info("Available targets:")
        for build_target, recipe in self.recipe_lut.items():
            target_display = f" -> {str(build_target)}"
            dep_display = f" <- {[str(dep) for dep in recipe.depends]}" if recipe.depends else ""
            plog.info(f"{target_display}: {dep_display}")

    def clean(self) -> None:
        self.recipe_lut.clear()
        self.ptm_srcs.clear()

# Create global instance and decorator
builder = BuildSystem.get_instance()
task = builder.task
target = builder.target
template = builder.template
