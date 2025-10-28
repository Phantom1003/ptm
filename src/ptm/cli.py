#!/usr/bin/env python3
"""
Phantom Make Command Line Interface

Usage:
    ptm <target> [options]

The tool reads `build.ptm` from the current directory and builds the specified target.
All command line arguments after the target name are available to the build script via Parameter.
"""

import os
import sys

from .system.logger import plog
from .syntax.include import include
from .system.builder import builder
from .syntax.param import Parameter


param = Parameter()

def main():
    args = sys.argv[1:]
    
    if len(args) > 0 and args[0] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)
    
    if len(args) == 0:
        target_name = "all"
        user_args = []
    elif args[0].startswith(('-')):
        target_name = "all"
        user_args = args
    else:    
        target_name = args[0]
        user_args = args[1:]

    i = 0
    while i < len(user_args):
        arg = user_args[i]
        if arg.startswith('-'):
            key = arg.lstrip('-')
            if i + 1 < len(user_args) and not user_args[i + 1].startswith('-'):
                param.add({key: user_args[i + 1]})
                i += 2
            else:
                param.add({key: True})
                i += 1

        else:
            print(f"Error: Invalid argument: {arg}")
            sys.exit(1)

    build_file = os.path.abspath('./build.ptm')
    if not os.path.exists(build_file):
        print(f"Error: build.ptm not found in current directory: {os.getcwd()}")
        sys.exit(1)

    plog.info(f"Loading build file: {build_file}")
    plog.info(f"Target: {target_name}")

    recipe = include(build_file, param)
    
    try:
        builder.build(target_name)
    except Exception as e:
        import traceback
        print(f"\nError building target '{target_name}':")
        print(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
