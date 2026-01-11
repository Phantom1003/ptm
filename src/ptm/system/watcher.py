import os
import sys
import time
import fcntl
import ctypes
import struct
import select
from abc import ABC, abstractmethod

from .logger import plog

class BaseWatcher(ABC):   
    @abstractmethod
    def add_watch(self, files: set[str]) -> bool:
        pass
    
    @abstractmethod
    def wait_change(self, timeout: float | None = None) -> set[str]:
        pass

    @abstractmethod
    def clean(self):
        pass


class InotifyWatcher(BaseWatcher):
    # Inotify event constants
    IN_ACCESS = 0x00000001
    IN_MODIFY = 0x00000002
    IN_ATTRIB = 0x00000004
    IN_CLOSE_WRITE = 0x00000008
    IN_CLOSE_NOWRITE = 0x00000010
    IN_OPEN = 0x00000020
    IN_MOVED_FROM = 0x00000040
    IN_MOVED_TO = 0x00000080
    IN_CREATE = 0x00000100
    IN_DELETE = 0x00000200
    IN_DELETE_SELF = 0x00000400
    IN_MOVE_SELF = 0x00000800
    IN_UNMOUNT = 0x00002000
    IN_Q_OVERFLOW = 0x00004000
    IN_IGNORED = 0x00008000
    IN_ONLYDIR = 0x01000000
    IN_DONT_FOLLOW = 0x02000000
    IN_EXCL_UNLINK = 0x04000000
    IN_MASK_ADD = 0x20000000
    IN_ISDIR = 0x40000000
    IN_ONESHOT = 0x80000000
    
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

    def _parse_event_mask(self, mask: int) -> list[str]:
        events = []
        if mask & self.IN_ACCESS:
            events.append("ACCESS")
        if mask & self.IN_MODIFY:
            events.append("MODIFY")
        if mask & self.IN_ATTRIB:
            events.append("ATTRIB")
        if mask & self.IN_CLOSE_WRITE:
            events.append("CLOSE_WRITE")
        if mask & self.IN_CLOSE_NOWRITE:
            events.append("CLOSE_NOWRITE")
        if mask & self.IN_OPEN:
            events.append("OPEN")
        if mask & self.IN_MOVED_FROM:
            events.append("MOVED_FROM")
        if mask & self.IN_MOVED_TO:
            events.append("MOVED_TO")
        if mask & self.IN_CREATE:
            events.append("CREATE")
        if mask & self.IN_DELETE:
            events.append("DELETE")
        if mask & self.IN_DELETE_SELF:
            events.append("DELETE_SELF")
        if mask & self.IN_MOVE_SELF:
            events.append("MOVE_SELF")
        if mask & self.IN_UNMOUNT:
            events.append("UNMOUNT")
        if mask & self.IN_Q_OVERFLOW:
            events.append("Q_OVERFLOW")
        if mask & self.IN_IGNORED:
            events.append("IGNORED")
        if mask & self.IN_ISDIR:
            events.append("ISDIR")
        if mask & self.IN_ONESHOT:
            events.append("ONESHOT")
        
        if not events:
            events.append(f"UNKNOWN(0x{mask:08x})")
        
        return events

    def add_watch(self, files: set[str]) -> bool:
        mask = self.IN_MODIFY | self.IN_ATTRIB | self.IN_MOVED_TO

        for f in files:
            wd = self.libc.inotify_add_watch(self._fd, f.encode(), mask)
            if wd >= 0:
                self._wd_map[wd] = f
            else:
                plog.warning(f"Failed to add inotify watch for {f}")

    def wait_change(self, timeout: float) -> set[str]:
        changed_files = {}
        ready, _, _ = select.select([self._fd], [], [], timeout)
        if ready:
            time.sleep(1)
            try:
                while True:
                    data = os.read(self._fd, 4096)
                    if not data:
                        break
                    # struct inotify_event { int wd; uint32_t mask; uint32_t cookie; uint32_t len; char name[]; }
                    event_struct = struct.Struct('iIII')
                    event_size = event_struct.size
                    
                    offset = 0
                    while offset < len(data):
                        if offset + event_size > len(data):
                            break
                        
                        wd, mask, cookie, name_len = event_struct.unpack_from(data, offset)
                        
                        if wd in self._wd_map:
                            file_path = self._wd_map[wd]
                            events = self._parse_event_mask(mask)
                            if file_path not in changed_files:
                                changed_files[file_path] = []
                            changed_files[file_path].extend(events)

                        offset += event_size + name_len
            except BlockingIOError:
                pass

        if changed_files:
            for file_path, events in changed_files.items():
                events_str = ', '.join(events)
                plog.debug(f"File changed: {file_path} [{events_str}]")
        
        return set(changed_files.keys())
    
    def clean(self):
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
    
    def wait_change(self, timeout: float | None = None) -> set[str]:
        return self._watcher.wait_change(timeout)
    
    def clean(self):
        self._watcher.clean()