#!/usr/bin/env python3
"""generate_latex.py — Converts data/resume.yaml into latex/sections/*.tex files."""

import os
import sys
import yaml


# ── LaTeX escaping ─────────────────────────────────────────────────────────────
_ESC_MAP = str.maketrans({
    '&':  r'\&',
    '%':  r'\%',
    '$':  r'\$',
    '#':  r'\#',
    '_':  r'\_',
    '{':  r'\{',
    '}':  r'\}',
    '~':  r'\textasciitilde{}',
    '^':  r'\textasciicircum{}',
    '\\': r'\textbackslash{}',
})

def esc(text):
    """Escape LaTeX special characters in a string."""
    if text is None:
        return ''
    return str(text).translate(_ESC_MAP)


# ── Section generators ─────────────────────────────────────────────────────────

def gen_header(data):
    p = data.get('personal', {})
    name    = esc(p.get('name', ''))
    title   = esc(p.get('title', ''))
    email   = esc(p.get('email', ''))
    phone   = esc(p.get('phone', ''))
    loc     = esc(p.get('location', ''))
    website = p.get('website', '')
    linkedin = p.get('linkedin', '')
    github   = p.get('github', '')
    summary  = esc(p.get('summary', ''))

    contact1_parts = [x for x in [email, phone, loc] if x]
    contact1 = r' \textbar\ '.join(contact1_parts)

    links = []
    if website:
        links.append(r'\href{' + website + r'}{' + esc(website.replace('https://', '').replace('http://', '')) + r'}')
    if linkedin:
        links.append(r'\href{https://' + linkedin.lstrip('https://') + r'}{LinkedIn}')
    if github:
        links.append(r'\href{https://' + github.lstrip('https://') + r'}{GitHub}')
    contact2 = r' \textbar\ '.join(links)

    lines = [r'\resumeheader{' + name + r'}{' + title + r'}{' + contact1 + r'}{' + contact2 + r'}']

    if summary:
        lines.append('')
        lines.append(r'\noindent ' + summary)

    return '\n'.join(lines)


def gen_experience(data):
    jobs = data.get('experience', [])
    if not jobs:
        return ''
    lines = [r'\section{Experience}']
    for job in jobs:
        title    = esc(job.get('role', ''))
        company  = esc(job.get('company', ''))
        location = esc(job.get('location', ''))
        start    = esc(job.get('start', ''))
        end      = esc(job.get('end', ''))
        dates    = f'{start} -- {end}' if start or end else ''
        desc     = esc(job.get('description', ''))
        bullets  = job.get('highlights', [])
        bullet_tex = '\n'.join(r'  \item ' + esc(b) for b in bullets)
        lines.append(r'\resumeentry{' + title + r'}{' + company + r'}{' +
                     location + r'}{' + dates + r'}{' + desc + r'}{' + bullet_tex + r'}')
    return '\n'.join(lines)


def gen_education(data):
    items = data.get('education', [])
    if not items:
        return ''
    lines = [r'\section{Education}']
    for edu in items:
        degree   = esc(edu.get('degree', ''))
        field    = esc(edu.get('field', ''))
        title    = f'{degree} in {field}' if field else degree
        inst     = esc(edu.get('institution', ''))
        location = esc(edu.get('location', ''))
        start    = esc(str(edu.get('start', '')))
        end      = esc(str(edu.get('end', '')))
        dates    = f'{start} -- {end}' if start or end else ''
        gpa      = edu.get('gpa')
        desc     = (r'GPA: ' + esc(str(gpa))) if gpa else ''
        bullets  = edu.get('highlights', [])
        bullet_tex = '\n'.join(r'  \item ' + esc(b) for b in bullets)
        lines.append(r'\resumeentry{' + title + r'}{' + inst + r'}{' +
                     location + r'}{' + dates + r'}{' + desc + r'}{' + bullet_tex + r'}')
    return '\n'.join(lines)


def gen_skills(data):
    skills = data.get('skills', {})
    if not skills:
        return ''
    lines = [r'\section{Skills}']
    for category, items in skills.items():
        if isinstance(items, list):
            value = ', '.join(esc(str(i)) for i in items)
        else:
            value = esc(str(items))
        lines.append(r'\skillrow{' + esc(category.replace('_', ' ').title()) + r'}{' + value + r'}')
    return '\n'.join(lines)


def gen_projects(data):
    projects = data.get('projects', [])
    if not projects:
        return ''
    lines = [r'\section{Projects}']
    for proj in projects:
        name    = esc(proj.get('name', ''))
        url     = proj.get('url', '')
        if url:
            name = r'\href{' + url + r'}{' + name + r'}'
        desc    = esc(proj.get('description', ''))
        tech    = proj.get('tech', [])
        tech_str = r'\textit{' + esc(', '.join(str(t) for t in tech)) + r'}' if tech else ''
        combined = ' --- '.join(x for x in [desc, tech_str] if x)
        bullets  = proj.get('highlights', [])
        bullet_tex = '\n'.join(r'  \item ' + esc(b) for b in bullets)
        lines.append(r'\resumeentry{' + name + r'}{}{}{}{' + combined + r'}{' + bullet_tex + r'}')
    return '\n'.join(lines)


def gen_certifications(data):
    certs = data.get('certifications', [])
    if not certs:
        return ''
    lines = [r'\section{Certifications}']
    for cert in certs:
        name   = esc(cert.get('name', ''))
        url    = cert.get('url', '')
        if url:
            name = r'\href{' + url + r'}{' + name + r'}'
        issuer = esc(cert.get('issuer', ''))
        date   = esc(str(cert.get('date', '')))
        lines.append(r'\resumeentry{' + name + r'}{' + issuer + r'}{}{' + date + r'}{}{}')
    return '\n'.join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

GENERATORS = {
    'header':         gen_header,
    'experience':     gen_experience,
    'education':      gen_education,
    'skills':         gen_skills,
    'projects':       gen_projects,
    'certifications': gen_certifications,
}

def main():
    yaml_path = 'data/resume.yaml'
    out_dir   = 'latex/sections'

    print(f'Loading {yaml_path} ...')
    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    os.makedirs(out_dir, exist_ok=True)

    for section, generator in GENERATORS.items():
        content = generator(data)
        out_path = os.path.join(out_dir, f'{section}.tex')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content + '\n')
        print(f'  wrote {out_path}')

    print('Done. All LaTeX sections regenerated.')


if __name__ == '__main__':
    main()
