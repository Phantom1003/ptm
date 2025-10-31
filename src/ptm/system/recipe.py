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
    """Represents a build target with both recipe and tree structure information."""
    
    def __init__(self, recipe: Callable, target: BuildTarget, depends: List[BuildTarget], external: bool = False, depth: int = 0):
        self.target = target
        self.depends = depends
        self.recipe = recipe
        self.external = external

        # Dependency Tree structure information
        self.depth = depth
        self.children: List['BuildRecipe'] = []

    def _get_timestamp(self, path: str) -> int:
        if os.path.exists(path):
            return os.stat(path).st_mtime_ns
        else:
            return 0

    def _outdate(self) -> bool:        
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
        if not self._outdate():
            plog.info(f"Target '{self.target}' is up to date")
        else:
            plog.info(f"Building target: {self.target}")
            # PTM feature: create target directory automatically
            if self.target.type == BuildTargetType.FILE and os.path.isabs(self.target.uid):
                os.makedirs(os.path.dirname(self.target.uid), exist_ok=True)
            if self.external:
                kwargs['jobs'] = jobs
            self.recipe(**kwargs)
    
    def add_child(self, child: 'BuildRecipe') -> None:
        """Add a child node to this node."""
        self.children.append(child)

    def __repr__(self) -> str:
        return f"BuildRecipe(target={self.target}, depth={self.depth})"


class DependencyTree:
    def __init__(self, valid_target: BuildTarget, recipe_lut: Dict[BuildTarget, BuildRecipe]):
        self.max_depth = 0
        self.recipe_lut: Dict[BuildTarget, BuildRecipe] = recipe_lut
        self.node_lut: Dict[BuildTarget, BuildRecipe] = {}
        self.node_depth_map: Dict[int, set[BuildRecipe]] = {}

        self.root = self._build_tree(valid_target, [], 0)
        self._compute_depth_map(self.root)

    def _build_tree(self, target: BuildTarget, history: List[BuildTarget], depth: int = 0) -> BuildRecipe | None:
        if target not in self.recipe_lut:        
            if target.type == BuildTargetType.FILE and os.path.exists(target.uid):
                    return None
            else:
                raise ValueError(f"Target '{target}' not found")

        plog.debug(f"Building tree node for target '{target}' at depth {depth}")

        if depth > self.max_depth:
            self.max_depth = depth

        if target in self.node_lut:
            prv_node = self.node_lut[target]
            if depth > prv_node.depth:
                self._update_subtree_depth(prv_node, depth)
            return prv_node

        target_recipe = self.recipe_lut[target]
        new_node = BuildRecipe(target_recipe.recipe, target_recipe.target, 
                            target_recipe.depends, external=target_recipe.external, depth=depth)
        self.node_lut[target] = new_node

        for dep in target_recipe.depends:
            if dep in history:
                plog.info(f"Circular dependency {target} <- {dep} dropped.")
                continue

            child_node = self._build_tree(dep, history + [target], depth + 1)
            if child_node is not None:
                new_node.add_child(child_node)

        return new_node

    def _update_subtree_depth(self, node: BuildRecipe, new_depth: int) -> None:
        plog.debug(f"Updating depth for node '{node.target}' from {node.depth} to {new_depth}")
        if new_depth <= node.depth:
            return

        if new_depth > self.max_depth:
            self.max_depth = new_depth

        node.depth = new_depth
        for child in node.children:
            self._update_subtree_depth(child, new_depth + 1)
    
    def _compute_depth_map(self, node: BuildRecipe | None) -> None:
        if node is None:
            return

        if node.depth not in self.node_depth_map:
            self.node_depth_map[node.depth] = set()
        self.node_depth_map[node.depth].add(node)
        
        for child in node.children:
            self._compute_depth_map(child)

    def get_build_order(self) -> List[BuildRecipe]:
        build_order: List[BuildRecipe] = []
        for depth in sorted(self.node_depth_map.keys(), reverse=True):
            build_order.extend(self.node_depth_map[depth])
        return build_order
    
    def __repr__(self) -> str:
        lines = [f"BuildTree (max_depth={self.max_depth})"]
        for depth in sorted(self.node_depth_map.keys()):
            nodes = self.node_depth_map[depth]
            lines.append(f"  Depth {depth}: {[node.target for node in nodes]}")
        return "\n".join(lines)
