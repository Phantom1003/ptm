import os
import signal
import multiprocessing as mp
from typing import List, Dict, Optional, Tuple

from ..system.logger import plog
from .recipe import BuildRecipe


def _proc_run_target(recipe: BuildRecipe, jobs_alloc: int) -> None:
    # os.setsid()
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

        self.modifies: set[str] = set()

    def _select_and_launch_tasks(self) -> None:
        look_ahead_limit = min(len(self.build_order), self.ptr + 2 * self.max_jobs)
        for i in range(self.ptr, look_ahead_limit):
            if self.cap <= 0:
                break
                
            target = self.build_order[i]

            if target not in self.done and target not in self.wip and self.remaining_deps.get(target, 0) == 0:
                if not target.outdate():
                    if target.recipe:
                        plog.info(f"Target '{target.target}' is up to date")
                    self._handle_completed_task(target, 0, 0)
                    continue

                if target.external:
                    if len(self.wip) == 0:
                        self._launch_task(target, self.max_jobs)
                    break
                else:
                    self._launch_task(target, 1)
                    continue
        

    def _launch_task(self, target: BuildRecipe, cores: int) -> None:
        plog.debug(f"Build {target.target} with {cores} cores")
        proc = mp.Process(target=_proc_run_target, args=(target, cores), name=f"ptm@{self.max_jobs - self.cap}")
        self.cap -= cores
        self.wip[target] = (proc, cores)
        proc.start()

    def _parse_wait_status(self, status):
        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        if os.WIFSIGNALED(status):
            return -os.WTERMSIG(status)
        return -1

    def _handle_completed_task(self, recipe: BuildRecipe, cores: int, exitcode: int) -> None:
        if recipe in self.wip:
            self.wip.pop(recipe)
            self.cap += cores
            self.modifies.add(recipe.target.uid)

        self.done.add(recipe)
        for t in self.build_order:
            if recipe.target in t.depends:
                self.remaining_deps[t] -= 1

        if exitcode == 0:
            if recipe.recipe:
                plog.debug(f"Target {recipe.target} completed successfully")
        else:
            plog.info(f"Target {recipe.target} failed with exit code {exitcode}")
            self.error = exitcode

    def _wait_for_completion(self) -> None:
        if not self.wip:
            return

        reaped_pid = None
        reaped_exitcode = None

        try:
            pid, status = os.waitpid(-1, 0)
            reaped_pid = pid
            reaped_exitcode = self._parse_wait_status(status)
        except ChildProcessError:
            pass

        for recipe, (proc, alloc) in list(self.wip.items()):
            if reaped_pid and proc.pid == reaped_pid:
                exitcode = reaped_exitcode
            elif not proc.is_alive():
                exitcode = proc.exitcode if proc.exitcode is not None else -1
            else:
                continue

            self._handle_completed_task(recipe, alloc, exitcode)

    def _advance_pointer(self) -> None:
        while self.ptr < len(self.build_order) and self.build_order[self.ptr] in self.done:
            self.ptr += 1

    def _cleanup(self) -> None:
        for proc, _ in self.wip.values():
            if proc.is_alive():
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

    def run(self) -> Tuple[int, set[str]]:
        try:
            while True:
                if self.error:
                    self._cleanup()
                    return self.error, self.modifies

                # TODO: better check logic
                if len(self.done) == len(self.build_order):
                    plog.debug("All targets completed")
                    return 0, self.modifies

                self._advance_pointer()
                self._select_and_launch_tasks()

                if len(self.wip) > 0:
                    self._wait_for_completion()

        except KeyboardInterrupt:
            plog.info("Build interrupted by user")
            self._cleanup()
            return 130, self.modifies
