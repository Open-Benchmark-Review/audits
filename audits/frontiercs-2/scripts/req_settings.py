# Summarise model-request settings from raw request bodies in an extracted trace dir.
import sys,os,json,glob,collections as C
root=sys.argv[1]
KEYS=['model','max_tokens','max_output_tokens','max_completion_tokens','reasoning_effort','reasoning','thinking','output_config','temperature','top_p','generationConfig','thinkingConfig','effort']
cnt=C.Counter(); n=0; bad=0; ex=None
for f in sorted(glob.glob(os.path.join(root,'**','*.request.bin'),recursive=True)):
    b=open(f,'rb').read()
    try: j=json.loads(b)
    except Exception:
        bad+=1; continue
    n+=1
    sig={}
    for k in KEYS:
        if k in j:
            v=j[k]
            if k=='reasoning' and isinstance(v,dict): v={kk:vv for kk,vv in v.items() if kk!='summary'}
            if k=='generationConfig' and isinstance(v,dict): v={kk:vv for kk,vv in v.items() if kk in('maxOutputTokens','thinkingConfig','temperature')}
            sig[k]=v
    cnt[json.dumps(sig,sort_keys=True)]+=1
print(f"{root}: {n} json requests ({bad} non-json)")
for s,c in cnt.most_common(6): print(f"   {c:5d} x {s[:300]}")
