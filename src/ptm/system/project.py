import os, sys
from enum import Enum, auto
from abc import ABC, abstractmethod
from pathlib import Path

from .logger import plog

class BaseRepository(ABC):
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = Path(path)

    @property
    @abstractmethod
    def version(self):
        pass

    def extern_cmd(self, cmd: str, wkdir: Path | None = None, ignore_error = True):
        if wkdir:
            old_cwd = os.getcwd()
            os.chdir(wkdir)

        ret = os.system(cmd)

        if wkdir:
            os.chdir(old_cwd)

        if not ignore_error and ret != 0:
            plog.error(f"Repo {self.name}: '{cmd}' failed")
            raise RuntimeError(f"External command failed with exit code {ret}")
    
    @abstractmethod
    def init(self):
        pass    

    @abstractmethod
    def sync(self):
        pass

    @abstractmethod
    def clean(self):
        pass

class GitRepositoryVersion:
    VALID_TYPES = {"tag", "branch", "commit"}
    
    def __init__(self, name:str, type: str, **args):
        self.type = type.lower()
        if self.type not in self.VALID_TYPES:
            raise ValueError(f"Unknown version type '{type}' for {name}")
        if self.type not in args:
            raise ValueError(f"Missing required information '{self.type}' for version type '{name}'")
        for attr_name in self.VALID_TYPES:
            if attr_name in args:
                setattr(self, attr_name, args[attr_name])

    @property
    def meta(self):
        return getattr(self, self.type)

class GitRepository(BaseRepository):
    def __init__(self, name: str, upstream: str, path: str, version: GitRepositoryVersion):
        super().__init__(name, path)
        self.upstream = upstream
        self._version = version

    @property
    def version(self):
        return self._version

    def __git_init(self):
        self.extern_cmd(f"git init {self.path}")
        self.extern_cmd(f"git remote add ptm_repo {self.upstream}", wkdir=self.path)

    def __git_fetch(self):
        self.extern_cmd(f"git fetch --depth=1 ptm_repo {self.version.meta}", wkdir=self.path)

    def __git_checkout(self):
        self.extern_cmd(f"git checkout --force {self.version.meta}", wkdir=self.path)

    def init(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
        self.__git_init()
        self.__git_fetch()
        self.__git_checkout()

    def sync(self):
        self.__git_fetch()
        self.__git_checkout()

    def clean(self):
        if os.path.exists(self.path):
            os.rmdir(self.path, recursive=True, ignore_errors=True)

class Project:
    def __init__(self, project_root: str, repos: list[BaseRepository]):
        self.path = Path(project_root)
        self.repos = repos

        self.repo_map = {}
        for repo in repos:
            self.repo_map[repo.name] = repo

    def init(self):
        for repo in self.repos:
            repo.init()

    def sync(self):
        for repo in self.repos:
            repo.sync()

    def clean(self):
        for repo in self.repos:
            repo.clean()
