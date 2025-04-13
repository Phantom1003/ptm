#!/usr/bin/env python3
from ptm import *

simple = include('simple.ptm')

if __name__ == '__main__':
    builder.build(simple.hello)
