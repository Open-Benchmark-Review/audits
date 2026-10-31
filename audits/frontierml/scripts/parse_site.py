"""Parse the pages www.frontierml.org serves (Next.js RSC payloads); no JavaScript is executed.

usage:
  python3 -I parse_site.py trials <data_trials.html> <out.json>   every trial record on /data/trials/
  python3 -I parse_site.py trajids <pages_dir> <out.json>         trial id -> trajectory id, from /trials/<id>/ pages
  python3 -I parse_site.py text <page.html>                       visible text of a page (used for grade pages)
"""
import glob
import html
import json
import os
import re
import sys


def rsc(s):
    """Concatenate the self.__next_f.push([1, "..."]) string chunks of a Next.js page."""
    return ''.join(json.loads(c) for c in re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)</script>', s, flags=re.S))


def trials(src, out):
    txt = rsc(open(src).read())
    recs = {}
    for m in re.findall(r'\{"id":"[a-z0-9-]+","task":[^{}]*\}', txt):
        r = json.loads(m)
        recs.setdefault(r['id'], r)
    json.dump(list(recs.values()), open(out, 'w'), indent=0)
    print(f'{len(recs)} trials -> {out}')


def trajids(pages, out):
    m = {}
    for f in sorted(glob.glob(os.path.join(pages, '*.html'))):
        ids = re.findall(r'\{"id":"([a-z0-9-]+-\d{8}[a-z0-9-]*)"', rsc(open(f).read()))
        m[os.path.basename(f)[:-5]] = ids[0] if ids else None
    json.dump(m, open(out, 'w'), indent=0)
    print(f'{len(m)} trajectory ids ({sum(v is None for v in m.values())} missing) -> {out}')


def text(src):
    s = open(src).read()
    s = re.sub(r'<(script|style).*?</\1>', '', s, flags=re.S)
    s = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)))
    i = s.find('Trial · ')
    return s[i:] if i >= 0 else s


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'trials':
        trials(sys.argv[2], sys.argv[3])
    elif cmd == 'trajids':
        trajids(sys.argv[2], sys.argv[3])
    elif cmd == 'text':
        print(text(sys.argv[2]))
