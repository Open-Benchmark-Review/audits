import json,sys,random,math,collections as C
d=json.load(open(sys.argv[1]))
P=C.defaultdict(dict)
for r in d['runs']: P[r['model_id']][r['task']]=1 if r['verdict']=='PASS' else 0
tasks=sorted({r['task'] for r in d['runs']})
order=sorted(P,key=lambda m:-sum(P[m].values()))
random.seed(0)
print("model        pass  rate   95% bootstrap CI (tasks resampled)")
for m in order:
    x=[P[m][t] for t in tasks]; n=len(x)
    bs=sorted(sum(random.choice(x) for _ in range(n))/n for _ in range(4000))
    print(f"{m:11s} {sum(x):3d}/48 {sum(x)/n:5.1%}  [{bs[100]:.1%}, {bs[3900]:.1%}]")
# exact McNemar for adjacent pairs among top 6
def mcnemar(a,b):
    b01=sum(1 for t in tasks if P[a][t]==1 and P[b][t]==0); b10=sum(1 for t in tasks if P[a][t]==0 and P[b][t]==1)
    n=b01+b10; k=min(b01,b10)
    p=min(1,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else 1
    return b01,b10,p
print("\nPaired exact McNemar (discordant tasks):")
top=['opus','gemini-agy','astra','terra','gemini','sol','glm','k31']
for i in range(len(top)):
    for j in range(i+1,len(top)):
        a,b=top[i],top[j]; x,y,p=mcnemar(a,b)
        if j==i+1 or (i==0): print(f"  {a:10s} vs {b:10s}: {x}-{y}  p={p:.3f}")
