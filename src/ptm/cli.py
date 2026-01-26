#!/usr/bin/env python3
"""
Phantom Make Command Line Interface

Usage:
    ptm [ptm args] [target] [target args]
    ptm [ptm args] -- [target args]
    ptm [target args]

PTM arguments:
    -d, --daemon    Watch mode: rebuild automatically when dependencies change
    -h, --help      Show this help message
    -j, --jobs N    Maximum parallel jobs (default: CPU count)

The tool reads `build.ptm` from the current directory and builds the specified target.
All target arguments are available to the build script via Parameter.
"""

import os
import sys

from .system.logger import plog
from .syntax.include import include
from .system.builder import builder
from .syntax.param import Parameter
from .system.scheduler import BuildScheduler
from .system.watcher import FileSystemWatcher
from .version import __version__

PTM_ARGS = [
    {'flags': ['-h', '--help'], 'key': 'help', 'action': 'store_true'},
    {'flags': ['-w', '--daemon'], 'key': 'daemon', 'action': 'store_true'},
    {'flags': ['-j', '--jobs'], 'key': 'jobs', 'action': 'store', 'type': int, 'default': os.cpu_count()},
]

def parse_ptm_args(args):
    ptm_args = {}
    target_name = None
    target_args = []

    flag_map = {}
    for arg_def in PTM_ARGS:
        for flag in arg_def['flags']:
            flag_map[flag] = arg_def
        if 'default' in arg_def:
            ptm_args[arg_def['key']] = arg_def['default']
        elif arg_def['action'] == 'store_true':
            ptm_args[arg_def['key']] = False

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in flag_map:
            arg_def = flag_map[arg]
            key = arg_def['key']
            if arg_def['action'] == 'store_true':
                ptm_args[key] = True
                i += 1
            elif arg_def['action'] == 'store':
                if '=' in arg:
                    _, value = arg.split('=', 1)
                    i += 1
                elif i+1 < len(args):
                    value = args[i+1]
                    i += 2
                else:
                    raise ValueError(f"Error: {arg} requires a value")
                ptm_args[key] = arg_def.get('type', str)(value)
        elif arg == '--' or not arg.startswith('-'):
            target_name = arg
            target_args = args[i+1:]
            break
        else:
            target_args = args[i:]
            break

    return ptm_args, target_name, target_args

def parse_target_args(args):
    param = Parameter()

    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('-'):
            key = arg.lstrip('-')
            if '=' in arg:
                key, value = key.split('=', 1)
                i += 1
            elif i+1 < len(args) and not args[i+1].startswith('-'):
                value = args[i+1]
                i += 2
            else:
                value = True
                i += 1
            param.add({key: value})
        else:
            raise ValueError(f"Unexpected positional argument: {arg}")

    return param

def main():
    args = sys.argv[1:]
    ptm_args, target_name, target_args = parse_ptm_args(args)

    plog.info(f"welcome to phantom-make {__version__}, Python {sys.version}")

    if target_name is None or target_name == "--":
        target_name = "all"
    
    if ptm_args.get('help'):
        print(__doc__)
        sys.exit(0)

    daemon_mode = ptm_args.get('daemon')
    max_jobs = ptm_args.get('jobs')

    if max_jobs < 1:
        raise ValueError("Number of jobs must be at least 1")

    param = parse_target_args(target_args)
    
    build_file = os.path.abspath('./build.ptm')
    if not os.path.exists(build_file):
        print(f"Error: build.ptm not found in current directory: {os.getcwd()}")
        sys.exit(1)

    plog.info(f"build target: {target_name}, top build file: {build_file}")
    if daemon_mode:
        plog.info("Daemon mode enabled")

    try:
        while True:
            _ = include(build_file, param)
            tree = builder.generate_dependency_tree(target_name)

            if daemon_mode:
                watcher = FileSystemWatcher(tree.generate_dependencies() | builder.ptm_srcs)

            scheduler = BuildScheduler(tree.generate_build_order(), max_jobs)
            exitcode, known_modifies = scheduler.run()

            if not daemon_mode:
                sys.exit(exitcode)
            else:
                if exitcode == 0:
                    plog.info("Build succeeded. Watching for changes...")
                else:
                    plog.info(f"Build failed with exit code {exitcode}. Watching for changes...")

                while True:
                    modifies = watcher.wait_change()

                    valid_modifies = modifies - known_modifies
                    if len(valid_modifies) > 0:
                        print("\033[2J\033[H", end="", flush=True)
                        plog.info("Rebuild triggered by:")
                        for f in valid_modifies:
                            plog.info(f"  - {f}")
                        break

                watcher.clean()
                builder.clean()

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"\nError building target '{target_name}':")
        print(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        if not daemon_mode:
            sys.exit(1)

if __name__ == '__main__':
    main()
