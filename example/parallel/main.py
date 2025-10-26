#!/usr/bin/env python3
from ptm import *

simple = include('parallel.ptm')

if __name__ == '__main__':
    builder.list_targets()
    builder.build(simple.all, 5)
