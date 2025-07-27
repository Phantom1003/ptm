import os

class _PTMEnvVar:
    """A simple wrapper for os.environ."""
    
    def __getitem__(self, key: str) -> str:
        """Get environment variable value."""
        return os.environ.get(key)
    
    def __setitem__(self, key: str, value: str) -> None:
        """Set environment variable value."""
        os.environ[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if environment variable exists."""
        return key in os.environ
    
    def __delitem__(self, key: str) -> None:
        """Delete environment variable."""
        del os.environ[key]
    
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    def get(self, key: str, default: str = None) -> str:
        """Get environment variable with default value."""
        return os.environ.get(key, default)

environ = _PTMEnvVar()
