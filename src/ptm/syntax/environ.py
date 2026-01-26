import os
from typing import Any

class EnvVar:
    
    def __getitem__(self, key: str) -> str:
        return os.environ.get(key, "")
    
    def __setitem__(self, key: str, value: str) -> None:
        os.environ[key] = value
    
    def __contains__(self, key: str) -> bool:
        return key in os.environ
    
    def __delitem__(self, key: str) -> None:
        del os.environ[key]
    
    def __getattr__(self, name: str) -> str:
        return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = str(value)

    def __delattr__(self, name: str) -> None:
        del self[name]

    def get(self, key: str, default: Any = None) -> str | None:
        return os.environ.get(key, str(default) if default else None)

environ = EnvVar()
