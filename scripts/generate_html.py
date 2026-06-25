#!/usr/bin/env python3
"""generate_html.py — Renders web/templates/index.html with data/resume.yaml and
copies web/static/ alongside the result into output/html/."""

import os
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader


def main():
    yaml_path    = 'data/resume.yaml'
    template_dir = 'web/templates'
    static_src   = 'web/static'
    out_dir      = 'output/html'
    static_dst   = os.path.join(out_dir, 'static')

    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template('index.html')

    os.makedirs(out_dir, exist_ok=True)
    out_html = os.path.join(out_dir, 'index.html')
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(template.render(**data))
    print(f'  wrote {out_html}')

    if os.path.isdir(static_src):
        if os.path.exists(static_dst):
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f'  copied static/ -> {static_dst}')

    print('\nDone. Open output/html/index.html in your browser.')


if __name__ == '__main__':
    main()
