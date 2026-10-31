"""Parse AI4AI-Bench case pages (lab.einsia.ai/ai4ai/trajectories/<case>/) into structured records.

usage: python3 -I parse_cases.py <cases_dir> <out_dir>

<out_dir>/cases.csv          one row per case: identity, status, checkpoint scores, selection, references, audit fields
<out_dir>/cases.json         same, plus every checkpoint row
<out_dir>/text/<case>.txt    the page's readable text (case brief and full semantic audit)
"""
import csv
import glob
import html
import json
import os
import re
import sys

AUDIT_FIELDS = ['Run outcome', 'Evaluation-boundary conduct', 'Execution compliance', 'Protocol exposure',
                'Observed use', 'Benchmark-side qualification', 'Result influence']


def text_of(fragment):
    x = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', '', fragment)
    x = re.sub(r'</(p|h\d|li|tr|div|section|td|th|span|table)>', '\n', x)
    x = re.sub(r'<[^>]+>', '', x)
    x = html.unescape(x)
    return '\n'.join(line.strip() for line in x.split('\n') if line.strip())


def num(x):
    try:
        return float(x.replace(',', '').replace('−', '-'))
    except (ValueError, AttributeError):
        return None


def checkpoint_rows(page):
    i = page.find('Official reduction rule')
    if i < 0:
        return [], None
    j = page.find('<table', i)
    k = page.find('</table>', j)
    if j < 0 or k < 0 or j > page.find('</section>', i):
        return [], None
    table = page[j:k]
    header = [text_of(h) for h in re.findall(r'(?s)<th[^>]*>(.*?)</th>', table)]
    rows = []
    for tr in re.findall(r'(?s)<tr[^>]*>(.*?)</tr>', table)[1:]:
        cells = [text_of(c) for c in re.findall(r'(?s)<td[^>]*>(.*?)</td>', tr)]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    metric = header[2] if len(header) > 2 else None
    return rows, metric


def after(t, label, n=1):
    lines = t.split('\n')
    for idx, line in enumerate(lines):
        if line == label and idx + n < len(lines):
            return lines[idx + n]
    return None


def parse(path):
    page = open(path, encoding='utf-8').read()
    case = os.path.basename(path)[:-5]
    harness, task, model, effort = case.split('__')
    t = text_of(page)
    rec = dict(case=case, harness=harness, task=task, model=model, effort=effort)
    m = re.search(r'← Trajectory Explorer [^\n]*\n([^\n]+)', t)
    rec['status'] = m.group(1) if m else None
    m = re.search(r'Result qualification\. ([^\n]*?)(?:\s{2,}|Recipe shift|\n)', t)
    rec['qualification'] = m.group(1).strip() if m else None
    m = re.search(r'Official reduction rule\n([^\n]+)', t)
    rec['reduction_rule'] = m.group(1) if m else None
    rows, metric = checkpoint_rows(page)
    rec['metric'] = metric
    rec['n_checkpoints'] = len(rows)
    ck = []
    for r in rows:
        vals = list(r.values())
        ck.append(dict(artifact=vals[0], progress=num(vals[1]), score=num(vals[2]), se=num(vals[3]), n=num(vals[4]),
                       role=vals[5]))
    rec['checkpoints'] = ck
    rec['best_retained'] = num(after(t, 'Best retained'))
    rec['final_checkpoint'] = num(after(t, 'Final checkpoint'))
    rec['checkpoint_rule'] = after(t, 'Checkpoint rule')
    rec['checkpoint_rule_note'] = after(t, 'Checkpoint rule', 2)
    rec['fixed_start'] = num(after(t, 'Fixed start'))
    rec['shipped_recipe'] = num(after(t, 'Shipped recipe'))
    for f in AUDIT_FIELDS:
        m = re.search(re.escape(f) + r'(Completed|Clean|Unknown|Confirmed|Not Observed|Observed|Violation|Failed|'
                      r'Not Applicable|Compliant|Noncompliant|Non-compliant|None|Partial|Suspected|Yes|No|[A-Z][a-z]+(?: [A-Za-z]+)?)'
                      r'(?:Whether|Observed|Timing|A finding)', t)
        rec[f] = m.group(1) if m else None
    m = re.search(r'Patch ID: (PATCH-[0-9a-f]+)', t)
    rec['patch_id'] = m.group(1) if m else None
    return rec, t


def main(cases_dir, out_dir):
    os.makedirs(os.path.join(out_dir, 'text'), exist_ok=True)
    recs = []
    for p in sorted(glob.glob(os.path.join(cases_dir, '*.html'))):
        rec, t = parse(p)
        recs.append(rec)
        open(os.path.join(out_dir, 'text', rec['case'] + '.txt'), 'w').write(t)
    json.dump(recs, open(os.path.join(out_dir, 'cases.json'), 'w'), indent=1)
    flat = []
    for r in recs:
        row = {k: v for k, v in r.items() if k != 'checkpoints'}
        row['checkpoint_scores'] = ';'.join(f"{c['progress']}:{c['score']}" for c in r['checkpoints'])
        flat.append(row)
    with open(os.path.join(out_dir, 'cases.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(flat[0]))
        w.writeheader()
        w.writerows(flat)
    print(f'{len(recs)} cases -> {out_dir}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
