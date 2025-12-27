import os
from pathlib import Path
from abc import ABC, abstractmethod

from .logger import plog

class BaseRepository(ABC):
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = Path(path)

    def extern_cmd(self, cmd: str, wkdir: Path | None = None, ignore_error: bool = False) -> int:
        if wkdir:
            old_cwd = os.getcwd()
            os.chdir(wkdir)
        plog.info(f"[{self.name}]:", cmd)
        ret = os.system(cmd)
        if wkdir:
            os.chdir(old_cwd)
        if ret != 0 and not ignore_error:
            raise RuntimeError(f"External command '{cmd}' failed with exit code {ret}")
        return ret

    @abstractmethod
    def sync(self):
        pass

    @abstractmethod
    def clean(self):
        pass

class LocalRepository(BaseRepository):
    def __init__(self, name: str, path: Path):
        super().__init__(name, path)

    def sync(self):
        if not os.path.exists(self.path):
            raise RuntimeError(f"Local repository path '{self.path}' does not exist")

    def clean(self):
        plog.info(f"Skip clean operation for local repository '{self.name}'")

class ArchiveRepository(BaseRepository):
    def __init__(self, name: str, path: Path, url: str):
        super().__init__(name, path)
        self.url = url
        self.archive = self.path / os.path.basename(self.url)

    def sync(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
    
        if not os.path.exists(self.archive):
            ret = self.extern_cmd(f"curl -C - -o {self.archive} {self.url}", ignore_error=True)
            if ret != 0:
                os.remove(self.archive)
        if str(self.archive).endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz', '.tar')):
            self.extern_cmd(f"tar -xf {self.archive} -C {self.path}")
        elif str(self.archive).endswith('.zip'):
            self.extern_cmd(f"unzip -o {self.archive} -d {self.path}")

    def clean(self):
        if os.path.exists(self.path):
            os.rmdir(self.path, recursive=True, ignore_errors=True)
            os.remove()

class GitRepository(BaseRepository):
    def __init__(self, name: str, path: Path, url: str, type: str, meta: str):
        super().__init__(name, path)
        self.url = url
        self.type = type
        self.meta = meta

    def __git_init(self):
        self.extern_cmd(f"git init {self.path}")
        self.extern_cmd(f"git remote add ptm_repo {self.url}", wkdir=self.path)

    def __git_fetch(self):
        self.extern_cmd(f"git fetch --depth=1 ptm_repo {self.meta}", wkdir=self.path)

    def __git_checkout(self):
        self.extern_cmd(f"git checkout --force {self.meta}", wkdir=self.path)

    def sync(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
        if not os.path.exists(self.path / ".git"):
            self.__git_init()
        self.__git_fetch()
        self.__git_checkout()

    def clean(self):
        if os.path.exists(self.path):
            os.rmdir(self.path, recursive=True, ignore_errors=True)

# {
#     name: starship
#     version: 1.0
#     repository: [
#         {
#             name: starship
#             type: git
#             commit: "a1b2c3d4e5f6g7h8i9j0"
#             url: "https://github.com/example/starship.git"
#             path: repo/starship
#         },
#         {
#             name: rss
#             type: local
#             path: /opt/rss
#         }
#         {
#             name: toolchain
#             type: archive
#             url: "https://example.com/toolchain.zip"
#             path: toolchain
#         }
#     ]
# }

class Project:
    def __init__(self, project_root: str, raw: dict, select_repos: list[str] | None = None):
        self.project_root = Path(project_root)
        self.name = raw.get("name", None)
        self.version = raw.get("version", None)

        self.repos = []
        self.repo_map = {}
        
        for repo in raw.get("repository", []):
            if select_repos is not None and repo.get("name", None) not in select_repos:
                continue
            repo_type = repo.get("type", "local").lower()
            if repo_type not in {"local", "git", "archive"}:
                raise ValueError(f"Unknown repository type '{repo_type}'")
            repo_handler = getattr(self, f"_add_{repo_type}_repo")
            repo_handler(repo)

    def __gen_path(self, path: str | None) -> Path:
        if path is None:
            raise ValueError(f"Project {self.name} has a repository with no path specified")
        if not os.path.isabs(path):
            path = self.project_root / path
        return path

    def _add_local_repo(self, repo_data: dict):
        path = self.__gen_path(repo_data.get("path", None))
        name = repo_data.get("name", str(path))

        repo = LocalRepository(name, path)
        self.repos.append(repo)
        self.repo_map[name] = repo

    def _add_archive_repo(self, repo_data: dict):
        path = self.__gen_path(repo_data.get("path", None))
        name = repo_data.get("name", str(path))
        url = repo_data.get("url", None)

        if not url:
            raise ValueError(f"ArchiveRepository {name} has no url")

        repo = ArchiveRepository(name, path, url)
        self.repos.append(repo)
        self.repo_map[name] = repo
    
    def _add_git_repo(self, repo_data: dict):
        path = self.__gen_path(repo_data.get("path", None))
        name = repo_data.get("name", str(path))
        url = repo_data.get("url", None)

        if not url:
            raise ValueError(f"GitRepository {name} has no url")
        if "commit" in repo_data:
            version_type = "commit"
            version_meta = repo_data["commit"]
        elif "tag" in repo_data:
            version_type = "tag"
            version_meta = repo_data["tag"]
        elif "branch" in repo_data:
            version_type = "branch"
            version_meta = repo_data["branch"]
        else:
            raise ValueError(f"GitRepository {name} has no valid version info")

        repo = GitRepository(name, path, url, version_type, version_meta)
        self.repos.append(repo)
        self.repo_map[name] = repo

    def sync(self, select_repos: list[str] | None = None): 
        for repo in self.repos:
            if select_repos is not None and repo.name not in select_repos:
                continue
            repo.sync()

    def clean(self, select_repos: list[str] | None = None):
        for repo in self.repos:
            if select_repos is not None and repo.name not in select_repos:
                continue
            repo.clean()

    def get_repo_path(self, repo_name: str) -> Path:
        if repo_name not in self.repo_map:
            raise KeyError(f"Repository '{repo_name}' not found in project '{self.name}'")
        return self.repo_map[repo_name].path

    def __getitem__(self, repo_name: str) -> Path:
        return self.get_repo_path(repo_name)
