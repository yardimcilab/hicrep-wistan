#!usr/bin/env python

from sys import stdin
from statistics import mean
from .scc_scores import get_scc_scores
from click import echo

if __name__ == "__main__":
    echo(mean(get_scc_scores(stdin.read())), nl=False)