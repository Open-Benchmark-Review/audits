import json,csv,sys
d=json.load(open(sys.argv[1])); log=list(csv.DictReader(open(sys.argv[2])))
counted={r['task_id'] for r in log if r['counted_toward_threshold']=='yes'}
P={}
for r in d['runs']: P.setdefault(r['model_id'],{})[r['task']]=r['verdict']=='PASS'
tasks=sorted({t for m in P for t in P[m]}); clean=[t for t in tasks if t not in counted]
# targeted corrections: remove confirmed hack passes; add progent post-fix flips
adj={m:dict(v) for m,v in P.items()}
adj['gemini']['dynamic_tanh']=False; adj['gemini']['detok_latent_denoising']=False
for m in ('opus','ds','qwen'): adj[m]['progent_privilege_control']=True
names={'opus':'Claude Opus 5.5','gemini-agy':'Gemini 4 Argon (Antigravity)','astra':'GPT-6 Astra','gemini':'Gemini 4 Argon (Pi)','terra':'GPT-6.1 Terra','sol':'GPT-6.1 Sol','glm':'GLM 5.3','k31':'Kimi K3.1 Pro','k3':'Kimi K3','wonder':'Muse Wonder 1.0','ds1017':'DeepSeek V4.1 Flash 1017','ds':'DeepSeek V4.1 Flash','muse':'Muse Spark 1.3','glmf':'GLM 5.3 Flash','qwen':'Qwen 3.8 Max','step':'Step 5 Preview','k27':'Kimi K2.7'}
print(f"{len(counted)} counted tasks, {len(clean)} clean tasks")
print("| Entry | Published pass rate (48) | Targeted corrections (48) | Pass rate on the 25 tasks without a counted defect |")
print("|---|---|---|---|")
for m in sorted(P,key=lambda m:-sum(P[m].values())):
    a=sum(P[m].values()); b=sum(adj[m].values()); c=sum(P[m][t] for t in clean)
    print(f"| {names[m]} | {a}/48 ({a/48:.1%}) | {b}/48 ({b/48:.1%}) | {c}/{len(clean)} ({c/len(clean):.0%}) |")
