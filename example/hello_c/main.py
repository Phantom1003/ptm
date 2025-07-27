#!/usr/bin/env python3
from ptm import *
import argparse
import os

cfg = include('hello_c.ptm')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--to', type=str, default='World', help='hello target')
    args = parser.parse_args()

    environ['TARGET'] = args.to

    if os.path.exists(cfg.hello_hdr):
        with open(cfg.hello_hdr, 'r') as f:
            hello_target = f.read().split('"')[1]

            if hello_target != args.to:
                os.remove(cfg.hello_hdr)

    builder.build(cfg.hello_run)
