import json,sys,collections as C
d=json.load(open(sys.argv[1]))
R=d['runs']
print(C.Counter(k for r in R for k in r).most_common())
per=C.defaultdict(C.Counter)
for r in R:
    m=r['model_id']; p=per[m]
    p['n']+=1; p['pass']+= r['verdict']=='PASS'
    p['state:'+str(r.get('platform_state'))]+=1
    p['no_final']+= r.get('final_submission_status')!='available'
    if r.get('failure_code'): p['fc:'+r['failure_code']]+=1
    p['src:'+r['result_source'][:40]]+=1
for m,p in sorted(per.items(),key=lambda x:-x[1]['pass']):
    print(m, dict(p))
