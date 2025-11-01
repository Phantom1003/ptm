import os
import multiprocessing as mp
from typing import List, Dict, Optional, Tuple

from ..system.logger import plog
from .recipe import BuildRecipe


def _proc_run_target(recipe: BuildRecipe, jobs_alloc: int) -> None:
    recipe.build(jobs=jobs_alloc)

class BuildScheduler:

    def __init__(self, build_order: List[BuildRecipe], max_jobs: int):
        self.max_jobs = max_jobs
        self.cap = max_jobs
        self.build_order = build_order

        self.remaining_deps: Dict[BuildRecipe, int] = {}
        for target in self.build_order:
            self.remaining_deps[target] = len(target.children)

        self.ptr = 0
        self.wip: Dict[BuildRecipe, Tuple[mp.Process, int]] = {}
        self.done: set[BuildRecipe] = set()
        self.error: Optional[int] = None

    def _select_and_launch_tasks(self) -> None:
        look_ahead_limit = min(len(self.build_order), self.ptr + 2 * self.max_jobs)
        for i in range(self.ptr, look_ahead_limit):
            if self.cap <= 0:
                break
                
            target = self.build_order[i]

            if target not in self.done and target not in self.wip and self.remaining_deps.get(target, 0) == 0:
                self._launch_task(target, 1)
                continue
            elif target.external:
                if len(self.wip) == 0:
                    self._launch_task(target, self.max_jobs)
                break

    def _launch_task(self, target: BuildRecipe, jobs: int) -> None:
        plog.debug(f"Started building {target.target} with {jobs} cores")
        proc = mp.Process(target=_proc_run_target, args=(target, jobs), name=f"ptm@{self.max_jobs - self.cap}")
        self.cap -= jobs
        self.wip[target] = (proc, jobs)
        proc.start()

    def _wait_for_completion(self) -> None:
        if not self.wip:
            return

        try:
            pid, status = os.waitpid(-1, 0)
        except ChildProcessError:
            for recipe, (proc, alloc) in list(self.wip.items()):
                if not proc.is_alive():
                    exitcode = proc.exitcode if proc.exitcode is not None else -1
                    self.wip.pop(recipe)
                    self.cap += alloc
                    
                    if exitcode == 0:
                        self.done.add(recipe)
                        plog.debug(f"Completed {recipe.target}")

                        for t in self.build_order:
                            if recipe.target in t.depends:
                                self.remaining_deps[t] -= 1
                    else:
                        plog.info(f"Target {recipe.target} failed with exit code {exitcode}")
                        self.error = exitcode
            return

        if os.WIFEXITED(status):
            exitcode = os.WEXITSTATUS(status)
        elif os.WIFSIGNALED(status):
            exitcode = -os.WTERMSIG(status)
        else:
            exitcode = -1

        for recipe, (proc, alloc) in list(self.wip.items()):
            if proc.pid == pid:
                self.wip.pop(recipe)
                self.cap += alloc
                
                if exitcode == 0:
                    self.done.add(recipe)
                    plog.debug(f"Completed {recipe.target}")

                    for t in self.build_order:
                        if recipe.target in t.depends:
                            self.remaining_deps[t] -= 1
                else:
                    plog.info(f"Target {recipe.target} failed with exit code {exitcode}")
                    self.error = exitcode
                return

    def _advance_pointer(self) -> None:
        while self.ptr < len(self.build_order) and self.build_order[self.ptr] in self.done:
            self.ptr += 1

    def run(self) -> int:
        """Main scheduling loop.
        
        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        while True:
            if self.error:
                return self.error
            
            if len(self.done) == len(self.build_order):
                plog.debug("All targets completed")
                return 0

            self._advance_pointer()
            self._select_and_launch_tasks()

            if len(self.wip) == 0:
                if len(self.done) < len(self.build_order):
                    plog.error("Deadlock detected: no runnable tasks but build incomplete")
                    return 1
                return 0

            if len(self.wip) > 0:
                self._wait_for_completion()
