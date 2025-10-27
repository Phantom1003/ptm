#!/usr/bin/env python3
"""
Phantom Make Command Line Interface

Usage:
    ptm <target> [options]

The tool reads `build.ptm` from the current directory and builds the specified target.
All command line arguments after the target name are available to the build script via ptm.argv.
"""

import os
import sys

from .logger import plog
from .include import include
from .builder import builder
from .param import Parameter

argv = None

class ArgvDict:
    def __init__(self, args):
        """Initialize with command line arguments (excluding program name and target)."""
        self._args = args
        self._dict = {}
        self._parse()
    
    def _parse(self):
        """Parse command line arguments into a dictionary."""
        i = 0
        while i < len(self._args):
            arg = self._args[i]
            if arg.startswith('-'):
                # Check if next argument exists and is not a flag
                if i + 1 < len(self._args) and not self._args[i + 1].startswith('-'):
                    self._dict[arg] = self._args[i + 1]
                    i += 2
                else:
                    self._dict[arg] = True
                    i += 1
            else:
                i += 1
    
    def __getitem__(self, key):
        """Get argument value by flag name."""
        return self._dict.get(key)
    
    def __contains__(self, key):
        """Check if flag is present."""
        return key in self._dict
    
    def get(self, key, default=None):
        """Get argument value with default."""
        return self._dict.get(key, default)
    
    def __repr__(self):
        return f"ArgvDict({self._dict})"
    
    def __str__(self):
        return str(self._dict)


def main():
    args = sys.argv[1:]
    
    if len(args) > 0 and args[0] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    if len(args) == 0:
        target_name = "all"
        user_args = []
    elif args[0].startswith(('-', '+')):
        target_name = "all"
        user_args = args
    else:    
        target_name = args[0]
        user_args = args[1:]

    global argv
    argv = ArgvDict(user_args)

    build_file = os.path.abspath('./build.ptm')

    if not os.path.exists(build_file):
        print(f"Error: build.ptm not found in current directory: {os.getcwd()}")
        sys.exit(1)

    try:
        include(build_file, param=Parameter())
    except Exception as e:
        print(f"Error loading build file: {e}")
        sys.exit(1)
    
    plog.info(f"Build target '{target_name}'")
    try:
        builder.build(target_name)
    except Exception as e:
        print(f"Error building target: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
