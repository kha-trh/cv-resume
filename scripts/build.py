#!/usr/bin/env python3
"""build.py — Optional CLI wrapper. Calls generate_latex.py, generate_html.py,
and xelatex in sequence. Useful for running inside the container directly."""

import argparse
import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description='Build resume PDF and/or HTML')
    parser.add_argument('--tex',  action='store_true', help='Generate LaTeX sections')
    parser.add_argument('--html', action='store_true', help='Generate HTML website')
    parser.add_argument('--pdf',  action='store_true', help='Compile PDF')
    args = parser.parse_args()

    do_all = not (args.tex or args.html or args.pdf)

    if args.tex or do_all:
        run('python3 scripts/generate_latex.py')

    if args.html or do_all:
        run('python3 scripts/generate_html.py')

    if args.pdf or do_all:
        run('cd latex && latexmk -xelatex -interaction=nonstopmode -silent main.tex')


if __name__ == '__main__':
    main()
