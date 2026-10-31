import json,sys,collections as C
d=json.load(open(sys.argv[1]))
runs={r['record_id']:r for r in d['runs']}
others=C.defaultdict(list)
for r in d['other_runs']: others[r['record_id']].append(r)
def scored(r): return r.get('verdict') in ('PASS','FAIL')
stats=C.Counter(); per_model=C.defaultdict(C.Counter)
rows=[]
for rid,a in runs.items():
    os_=[o for o in others.get(rid,[]) if scored(o)]
    if not os_: continue
    allr=sorted(os_+[a],key=lambda x:x['created_at'])
    is_latest = allr[-1] is a
    v=[x['verdict'] for x in allr]
    pas=sum(x=='PASS' for x in v)
    m=a['model_id']
    per_model[m]['records_multi']+=1
    per_model[m]['accepted_pass']+= a['verdict']=='PASS'
    per_model[m]['first_pass']+= allr[0]['verdict']=='PASS'
    per_model[m]['mean_pass']+= pas/len(v)
    per_model[m]['any_pass']+= pas>0
    per_model[m]['accepted_latest']+= is_latest
    per_model[m]['mixed']+= 0<pas<len(v)
    per_model[m]['mixed_accepted_pass']+= (0<pas<len(v)) and a['verdict']=='PASS'
    per_model[m]['mixed_expected_pass']+= (pas/len(v)) if 0<pas<len(v) else 0
    rows.append((rid,[ (x['created_at'][:16],x['verdict'],x is a) for x in allr]))
print(f"{'model':11s} multi acc_pass first_pass mean_pass any_pass acc_latest mixed mixed_accPASS mixed_expPASS")
tot=C.Counter()
for m,c in sorted(per_model.items()):
    print(f"{m:11s} {c['records_multi']:5d} {c['accepted_pass']:8d} {c['first_pass']:10d} {c['mean_pass']:9.1f} {c['any_pass']:8d} {c['accepted_latest']:10d} {c['mixed']:5d} {c['mixed_accepted_pass']:13d} {c['mixed_expected_pass']:13.1f}")
    tot.update(c)
print('TOTAL',dict(tot))
if len(sys.argv)>2:
    for rid,seq in rows:
        if len(set(v for _,v,_ in seq))>1: print(rid,seq)
