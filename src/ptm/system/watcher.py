import os
import sys
import time
import fcntl
import ctypes
import select
from abc import ABC, abstractmethod

from .logger import plog

class BaseWatcher(ABC):   
    @abstractmethod
    def add_watch(self, files: set[str]) -> bool:
        pass
    
    @abstractmethod
    def wait_change(self, timeout: float | None = None) -> bool:
        pass

    @abstractmethod
    def cleanup(self):
        pass


class InotifyWatcher(BaseWatcher):    
    def __init__(self):
        self._fd = None
        self._wd_map = {}
        self.libc = ctypes.CDLL(None)

        fd = self.libc.inotify_init()
        if fd < 0:
            raise RuntimeError("Failed to initialize inotify")

        self._fd = fd
        flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
        fcntl.fcntl(self._fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def add_watch(self, files: set[str]) -> bool:
        IN_MODIFY = 0x00000002
        IN_ATTRIB = 0x00000004
        IN_MOVED_TO = 0x00000080

        mask = IN_MODIFY | IN_ATTRIB | IN_MOVED_TO

        for f in files:
            wd = self.libc.inotify_add_watch(self._fd, f.encode(), mask)
            if wd >= 0:
                self._wd_map[wd] = f
            else:
                plog.warning(f"Failed to add inotify watch for {f}")

    def wait_change(self, timeout: float) -> bool:
        ready, _, _ = select.select([self._fd], [], [], timeout)
        if ready:
            time.sleep(1)
            try:
                while True:
                    if not os.read(self._fd, 4096):
                        break
            except BlockingIOError:
                pass
        return False
    
    def cleanup(self):
        if self._fd:
            os.close(self._fd)

class FileSystemWatcher:   
    def __init__(self, files: set[str] | None = None):
        self._watcher = self._create_watcher()

        if files:
            self.add_watch(files)

    def _create_watcher(self) -> BaseWatcher:
        match sys.platform:
            case 'linux':
                watcher = InotifyWatcher()
            case _:
                raise NotImplementedError("Unsupported platform, please disable daemon mode and try again.")
        return watcher

    def add_watch(self, files: set[str]):
        self._watcher.add_watch(files)
    
    def wait_change(self, timeout: float | None = None) -> bool:
        return self._watcher.wait_change(timeout)
