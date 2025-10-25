import os
import functools
from typing import List, Dict, Callable, Any, Optional, Union
from collections import defaultdict

from .logger import plog

def _get_timestamp(path: str) -> int:
    if os.path.exists(path):
        return os.stat(path).st_mtime_ns
    else:
        return 0

class BuildRecipe:
    """Represents a build target with both recipe and tree structure information."""
    
    def __init__(self, recipe: Callable, target: str, depends: List[str], *, external: bool = False, depth: int = 0):
        # Build Recipe information
        self.target = target
        self.depends = depends
        self.recipe = recipe
        self.external = external

        # Dependency Tree structure information
        self.depth = depth
        self.children: List['BuildRecipe'] = []

    def _outdate(self) -> bool:
        target_timestamp = _get_timestamp(self.target)
        if target_timestamp == 0:
            return True

        for depend in self.depends:
            if _get_timestamp(depend) >= target_timestamp:
                return True

        return False

    def build(self, jobs: int = 1, **kwargs) -> Any:
        if not self._outdate():
            plog.info(f"Target '{self.target}' is up to date")
        else:
            plog.info(f"Building target: {self.target}")
            if os.path.isabs(self.target):
                os.makedirs(os.path.dirname(self.target), exist_ok=True)

            if self.external:
                kwargs['jobs'] = jobs

            self.recipe(**kwargs)
    
    def add_child(self, child: 'BuildRecipe') -> None:
        """Add a child node to this node."""
        self.children.append(child)

    def __repr__(self) -> str:
        return f"BuildRecipe(target={self.target}, depth={self.depth})"


class DependencyTree:
    def __init__(self, valid_target_name: str, target_lut: Dict[str, BuildRecipe]):
        self.max_depth = 0
        self.recipe_lut: Dict[str, BuildRecipe] = target_lut
        self.node_lut: Dict[str, BuildRecipe] = {}
        self.node_depth_map: Dict[int, List[BuildRecipe]] = {}

        self.root = self._build_tree(valid_target_name, [], 0)
        self._compute_depth_map(self.root)

    def _build_tree(self, target: str, history: List[str], depth: int = 0) -> BuildRecipe | None:
        if target not in self.recipe_lut:
            if not os.path.exists(target):
                raise ValueError(f"Target '{target}' not found")
            return None

        if depth > self.max_depth:
            self.max_depth = depth

        if target in self.node_lut:
            prv_node = self.node_lut[target]
            if depth > prv_node.depth:
                prv_node.depth = depth
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
    
    def _update_subtree_depth(self, node: BuildRecipe, parent_depth: int) -> None:
        new_depth = parent_depth + 1
        if new_depth <= node.depth:
            return

        if new_depth > self.max_depth:
            self.max_depth = new_depth
        
        node.depth = new_depth
        for child in node.children:
            self._update_subtree_depth(child, new_depth)
    
    def _compute_depth_map(self, node: BuildRecipe | None) -> None:
        if node is None:
            return

        if node.depth not in self.node_depth_map:
            self.node_depth_map[node.depth] = []
        self.node_depth_map[node.depth].append(node)
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
