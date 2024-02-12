#!usr/bin/env python

from sys import stdin
from click import echo

def get_scc_scores(raw_hicrep_output):
    lines = raw_hicrep_output.split('\n')
    scc_scores = []
    for line in lines:
        try:
            scc_scores.append(float(line))
        except ValueError:
            continue
    return scc_scores

if __name__ == "__main__":
    echo(get_scc_scores(stdin.read()), nl=False)