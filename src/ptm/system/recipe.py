import os
from enum import Enum
from typing import List, Dict, Callable, Any, Union

from ..system.logger import plog

class BuildTargetType(Enum):
    FILE = "file"
    TASK = "func"

class BuildTarget:
    def __init__(self, target: Union[str, Callable]):
        if callable(target):
            self.type = BuildTargetType.TASK
            self.name = target.__name__
            self.uid = id(target)
            self.meta = f"{target.__code__.co_filename}@{target.__code__.co_firstlineno}"
        else:
            self.type = BuildTargetType.FILE
            self.name = target
            self.uid = os.path.abspath(target)

    def __hash__(self):
        return hash((self.type, self.uid))
    
    def __eq__(self, other):
        if not isinstance(other, BuildTarget):
            return False
        if self.type != other.type:
            return False
        if self.name != other.name:
            return False
        if self.uid != other.uid:
            return False
        return True
    
    def __str__(self):
        if self.type == BuildTargetType.TASK:
            return f"{self.name} [{self.meta}]"
        elif self.type == BuildTargetType.FILE:
            return self.uid

    def __repr__(self):
        return self.__str__()


class BuildRecipe:
    def __init__(self, recipe: Callable, target: BuildTarget, depends: List[BuildTarget], external: bool = False, depth: int = -1):
        self.target = target
        self.depends = depends
        self.recipe = recipe
        self.external = external

        # Dependency Graph
        self.depth = depth
        self.children: List['BuildRecipe'] = []

    def _get_timestamp(self, path: str) -> int:
        if os.path.exists(path):
            return os.stat(path).st_mtime_ns
        else:
            return 0

    def outdate(self) -> bool:        
        if self.target.type == BuildTargetType.TASK:
            return True

        target_timestamp = self._get_timestamp(self.target.uid)
        if target_timestamp == 0:
            return True
        for depend in self.depends:
            if depend.type == BuildTargetType.TASK:
                return True
            if self._get_timestamp(depend.uid) >= target_timestamp:
                return True

        return False

    def build(self, jobs: int = 1, **kwargs) -> Any:
        if self.outdate():
            plog.info(f"Building target: {self.target}")
            if self.external:
                kwargs['jobs'] = jobs
            self.recipe(**kwargs)
    
    def add_child(self, child: 'BuildRecipe') -> None:
        self.children.append(child)

    def __repr__(self) -> str:
        return f"BuildRecipe(target={self.target}, depth={self.depth})"


class DependencyTree:
    def __init__(self, target: Union[str, Callable, BuildTarget], recipe_lut: Dict[BuildTarget, BuildRecipe]):
        self.max_depth = 0
        self.recipe_lut: Dict[BuildTarget, BuildRecipe] = recipe_lut
        self.depth_map: Dict[int, set[BuildRecipe]] = {}

        if not isinstance(target, BuildTarget):
            target = self._find_target(target)
        self.root = self._build_tree(target, [], 0)
        self._compute_depth_map(self.root)

    def _find_target(self, look_for: str | Callable) -> BuildTarget:
        if callable(look_for):
            look_for = look_for.__name__

        for build_target, _ in self.recipe_lut.items():
            if build_target.name == look_for:
                return build_target
            elif build_target.uid == look_for:
                return build_target

        raise ValueError(f"Target '{look_for}' not found")

    def _build_tree(self, target: BuildTarget, history: List[BuildTarget], depth: int = 0) -> BuildRecipe | None:
        plog.debug(f"Building tree node for target '{target}' at depth {depth}")

        if target not in self.recipe_lut:
            if target.type == BuildTargetType.FILE and os.path.exists(target.uid):
                leaf = BuildRecipe(None, target, [], depth=depth)
                self.recipe_lut[target] = leaf
                return leaf
            else:
                raise ValueError(f"Target '{target}' not found")
        
        target_recipe = self.recipe_lut[target]

        if depth > self.max_depth:
            self.max_depth = depth

        if target_recipe.depth >= 0:
            if depth > target_recipe.depth:
                self._update_subtree_depth(target_recipe, depth)
            return target_recipe

        target_recipe = self.recipe_lut[target]
        target_recipe.depth = depth

        for dep in target_recipe.depends:
            if dep in history:
                plog.info(f"Circular dependency {target} <- {dep} dropped.")
                continue

            child_node = self._build_tree(dep, history + [target], depth + 1)
            target_recipe.add_child(child_node)

        return target_recipe

    def _update_subtree_depth(self, node: BuildRecipe, new_depth: int) -> None:
        plog.debug(f"Updating depth for node '{node.target}' from {node.depth} to {new_depth}")
        if new_depth <= node.depth:
            return

        if new_depth > self.max_depth:
            self.max_depth = new_depth

        node.depth = new_depth
        for child in node.children:
            self._update_subtree_depth(child, new_depth + 1)
    
    def _compute_depth_map(self, node: BuildRecipe) -> None:
        if node.depth not in self.depth_map:
            self.depth_map[node.depth] = set()
        self.depth_map[node.depth].add(node)
        
        for child in node.children:
            self._compute_depth_map(child)

    def generate_build_order(self) -> List[BuildRecipe]:
        build_order: List[BuildRecipe] = []
        for depth in sorted(self.depth_map.keys(), reverse=True):
            build_order.extend(self.depth_map[depth])
        plog.debug(f"Generated build order: {build_order}")
        return build_order
    
    def generate_dependencies(self) -> set:
        dep_src = set()
        for node in self.recipe_lut.values():
            for dep in node.depends:
                if dep.type == BuildTargetType.FILE and os.path.exists(dep.uid):
                    dep_src.add(dep.uid)
        return dep_src

    def __repr__(self) -> str:
        lines = [f"BuildTree (max_depth={self.max_depth})"]
        for depth in sorted(self.depth_map.keys()):
            nodes = self.depth_map[depth]
            lines.append(f"  Depth {depth}: {[node.target for node in nodes]}")
        return "\n".join(lines)
