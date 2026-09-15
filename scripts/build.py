#!/usr/bin/env python3
"""
File Name: scripts/build.py

Description:
    Optional standalone Python CLI build wrapper. Sequentially coordinates LaTeX
    section generation (generate_latex.py), HTML site rendering (generate_html.py),
    and master PDF compilation (latexmk -xelatex) for development environments.

How to Use:
    Run inside the container or a properly configured local Python+LaTeX environment:
        python3 scripts/build.py           # Build all targets (LaTeX + HTML + PDF)
        python3 scripts/build.py --tex     # Generate LaTeX section files only
        python3 scripts/build.py --html    # Generate HTML website only
        python3 scripts/build.py --pdf     # Compile XeLaTeX master PDF
    Prerequisites:
        - Python 3.x with pyyaml and jinja2
        - XeLaTeX and latexmk (for --pdf or full builds)

Where It Is Used:
    - Used as a direct CLI build entry point inside Docker or dev containers.
    - Interacts with scripts/generate_latex.py, scripts/generate_html.py, and latex/main.tex.
"""

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
