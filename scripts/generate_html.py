#!/usr/bin/env python3
"""
File Name: scripts/generate_html.py

Description:
    Renders the Jinja2 template at web/templates/index.html using content from
    data/resume.yaml and writes the resulting static resume website to output/html/index.html.
    Also synchronizes static assets (CSS, JS, images) from web/static/ to output/html/static/.

How to Use:
    Execute directly via Python or through build orchestration:
        python3 scripts/generate_html.py
        ./build_all.sh --html
    Prerequisites:
        - Python 3.x
        - PyYAML and Jinja2 packages (pip install pyyaml jinja2)
        - Valid data/resume.yaml source file and web/templates/index.html template

Where It Is Used:
    - Called by build_all.sh during the HTML website generation stage.
    - Called by scripts/build.py during direct CLI builds.
    - Populates the output/html/ web bundle for browser viewing and static hosting.
"""

import os
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader


def main():
    yaml_path    = 'data/resume.yaml'
    config_path  = 'config/build.yaml'
    template_dir = 'web/templates'
    static_src   = 'web/static'
    out_dir      = 'output/html'
    static_dst   = os.path.join(out_dir, 'static')

    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    active_sections = None
    if os.path.exists(config_path):
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            active_sections = config.get('sections')

    data['active_sections'] = active_sections

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
