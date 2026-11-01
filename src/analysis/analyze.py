"""Deterministic, auditable analysis; no model calls or model-result-driven tuning."""
from pathlib import Path
import argparse,json,csv,collections,statistics,math,random,hashlib
ROOT=Path(__file__).resolve().parents[2]
MODELS=['qwen05','qwen15','smol17'];METHODS=['random','coverage','tool_name','policy'];BUDGETS=[1,2,4,8]

def write_csv(path,rows):
 if not rows:return
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def exact_p(a,b):
 n=a+b
 return 1.0 if n==0 else min(1.0,2*sum(math.comb(n,k) for k in range(min(a,b)+1))/(2**n))

def cluster_interval(pairs,repetitions=5000):
 # Resample fixed case clusters, then their seeds. Exploratory only with 5 cases.
 bycase=collections.defaultdict(list)
 for case,d in pairs:bycase[case].append(d)
 if not bycase:return None,None
 rng=random.Random(8031);cases=list(bycase);vals=[]
 for _ in range(repetitions):
  ds=[]
  for c in rng.choices(cases,k=len(cases)):
   ds.extend(rng.choices(bycase[c],k=len(bycase[c])))
  vals.append(statistics.mean(ds))
 vals.sort();return vals[int(.025*repetitions)],vals[int(.975*repetitions)]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--partial',action='store_true');args=ap.parse_args()
 out=ROOT/'results'/'processed';out.mkdir(exist_ok=True)
 campaigns=[];controls=[];overview=[];allrows=[];costs=[]
 for model in MODELS:
  base=ROOT/'results'/'raw'/'primary'/model
  if not (base/'manifest.json').exists():
   if args.partial:continue
   raise RuntimeError('Incomplete model: '+model)
  meta=json.loads((base/'manifest.json').read_text());assert not meta['smoke'] and meta['split']=='evaluation'
  rows=[json.loads(l) for l in (base/'episodes.jsonl').read_text().splitlines()]
  inf=[json.loads(l) for l in (base/'inferences.jsonl').read_text().splitlines()];calls={r['id']:r for r in inf}
  assert len(rows)==850,(model,len(rows));assert len(set(x['id'] for x in rows))==850
  assert len(inf)==meta['actual_inference_records'];allrows.extend(rows)
  ctrl={(r['case'],r['generation_seed'],r['mode']):r for r in rows if r['mode'] in ('clean','benign')}
  for mode in ['clean','benign']:
   rr=[r for r in rows if r['mode']==mode]
   controls.append({'model':model,'mode':mode,'n':len(rr),'valid':sum(r['valid_pipeline'] for r in rr),'useful':sum(r['final']['useful'] for r in rr),'violations':sum(r['final']['violation'] for r in rr)})
  groups=collections.defaultdict(list)
  for r in rows:
   if r['mode'] in METHODS:groups[(r['case'],r['campaign_seed'],r['mode'])].append(r)
  for (case,seed,method),rr in groups.items():
   rr.sort(key=lambda x:x['iteration']);assert [r['iteration'] for r in rr]==list(range(8))
   clean=ctrl[(case,seed,'clean')];benign=ctrl[(case,seed,'benign')]
   qualified=clean['valid_pipeline'] and clean['final']['useful'] and not clean['final']['violation']
   first=next((i+1 for i,r in enumerate(rr) if r['final']['violation']),9)
   curves={b:int(any(r['final']['violation'] for r in rr[:b])) for b in BUDGETS}
   campaigns.append({'model':model,'case':case,'seed':seed,'method':method,'qualified_clean':int(qualified),'benign_violation':int(benign['final']['violation']),'detected':int(first<=8),'first_capped':first,'auc':sum(curves.values())/4,'valid_episodes':sum(r['valid_pipeline'] for r in rr),'unique_contexts':len({r['payload'] for r in rr}),'unique_decision_signatures':len({tuple(r['signature']) for r in rr}),**{'detected_at_'+str(b):v for b,v in curves.items()}})
   logical_tokens=sum(calls[c['inference_id']]['usage']['total_tokens'] for r in rr for c in r['calls'])
   costs.append({'model':model,'case':case,'seed':seed,'method':method,'logical_episodes':8,'logical_role_invocations':sum(len(r['calls']) for r in rr),'uncached_equivalent_total_tokens':logical_tokens,'actual_new_inference_references':sum(not c['cache_hit'] for r in rr for c in r['calls'])})
  overview.append({'model':model,'logical_episodes':len(rows),'logical_role_invocations':sum(len(r['calls']) for r in rows),'unique_actual_inferences':len(inf),'cache_hits':sum(c['cache_hit'] for r in rows for c in r['calls']),'actual_prompt_tokens':sum(i['usage']['prompt_tokens'] for i in inf),'actual_completion_tokens':sum(i['usage']['completion_tokens'] for i in inf),'sum_inference_seconds':sum(i['seconds'] for i in inf),'valid_episodes':sum(r['valid_pipeline'] for r in rows),'distinct_contexts':len({(r['case'],r['payload']) for r in rows if r['mode'] in METHODS})})
 summaries=[];curves=[];comparisons=[]
 for model in MODELS:
  for method in METHODS:
   rr=[r for r in campaigns if r['model']==model and r['method']==method]
   if not rr:continue
   qq=[r for r in rr if r['qualified_clean']]
   summaries.append({'model':model,'method':method,'campaigns':len(rr),'raw_detected':sum(r['detected'] for r in rr),'qualified_campaigns':len(qq),'qualified_detected':sum(r['detected'] for r in qq),'raw_detection_rate':statistics.mean(r['detected'] for r in rr),'qualified_detection_rate':statistics.mean(r['detected'] for r in qq) if qq else None,'mean_capped_first':statistics.mean(r['first_capped'] for r in rr),'qualified_mean_capped_first':statistics.mean(r['first_capped'] for r in qq) if qq else None,'auc':statistics.mean(r['auc'] for r in rr),'valid_episodes':sum(r['valid_episodes'] for r in rr),'logical_episodes':8*len(rr)})
   for b in BUDGETS:curves.append({'model':model,'method':method,'budget':b,'detected':sum(r['detected_at_'+str(b)] for r in rr),'campaigns':len(rr),'qualified_detected':sum(r['detected_at_'+str(b)] for r in qq),'qualified_campaigns':len(qq)})
  for comparator in ['random','coverage','tool_name']:
   p={(r['case'],r['seed']):r for r in campaigns if r['model']==model and r['method']=='policy'}
   q={(r['case'],r['seed']):r for r in campaigns if r['model']==model and r['method']==comparator}
   if not p:continue
   for qualified in [False,True]:
    keys=[k for k in p if not qualified or p[k]['qualified_clean']]
    aa=sum(p[k]['detected'] and not q[k]['detected'] for k in keys);bb=sum(q[k]['detected'] and not p[k]['detected'] for k in keys)
    diffs=[(k[0],p[k]['detected']-q[k]['detected']) for k in keys]
    lo,hi=cluster_interval(diffs)
    comparisons.append({'model':model,'comparator':comparator,'stratum':'clean_valid_useful_safe' if qualified else 'all','pairs':len(keys),'case_clusters':len({k[0] for k in keys}),'policy_only':aa,'comparator_only':bb,'detection_difference':statistics.mean(d for _,d in diffs) if diffs else None,'cluster_ci_low':lo,'cluster_ci_high':hi,'exploratory_exact_discordance_p':exact_p(aa,bb) if keys else None,'note':'Resamples case clusters represented in the selected stratum; repeated seeds within fixed instances. Not a population confidence interval, equivalence test, or confirmatory hypothesis test.'})
 write_csv(out/'campaigns.csv',campaigns);write_csv(out/'controls.csv',controls);write_csv(out/'model_accounting.csv',overview);write_csv(out/'method_summary.csv',summaries);write_csv(out/'budget_curves.csv',curves);write_csv(out/'paired_comparisons.csv',comparisons);write_csv(out/'logical_costs.csv',costs)
 report={'models_complete':[o['model'] for o in overview],'total_logical_episodes':sum(o['logical_episodes'] for o in overview),'total_role_invocations':sum(o['logical_role_invocations'] for o in overview),'actual_unique_inferences':sum(o['unique_actual_inferences'] for o in overview),'controls':controls,'methods':summaries,'comparisons':comparisons,'scope':'Constructed finite-action three-role workflows; 5 fixed evaluation instances, 5 seeds, 8-query logical budget, exact-input memoization. No SOTA or production claim.'}
 (out/'summary.json').write_text(json.dumps(report,indent=2))
 lines=['# Expanded security-fuzzing study','',report['scope'],'','## Accounting','','| Model | Logical workflows | Fresh model inference records | Cache reuses | Valid workflows |','|---|---:|---:|---:|---:|']
 for o in overview:lines.append(f"| {o['model']} | {o['logical_episodes']} | {o['unique_actual_inferences']} | {o['cache_hits']} | {o['valid_episodes']} |")
 lines+=['','Logical episode counts are query budgets, not independent faults or fresh model calls. Cached roles refer to exact prior inputs, model hash and sampling seed. Per-method runtime is not compared because sequential shared caching makes it order-dependent. Token costs include both physical consumption and uncached-equivalent logical costs, separately labeled.','','## Clean and benign controls','','| Model | Control | n | Valid | Useful action | Security violations |','|---|---|---:|---:|---:|---:|']
 for c in controls:lines.append(f"| {c['model']} | {c['mode']} | {c['n']} | {c['valid']} | {c['useful']} | {c['violations']} |")
 lines+=['','## Main comparison','','| Model | Method | Detected / all campaigns | Detected / clean-qualified campaigns | Mean capped first |','|---|---|---:|---:|---:|']
 for s in summaries:lines.append(f"| {s['model']} | {s['method']} | {s['raw_detected']}/{s['campaigns']} | {s['qualified_detected']}/{s['qualified_campaigns']} | {s['mean_capped_first']:.2f} |")
 lines+=['','A clean-qualified campaign has a valid, useful and safe matched clean control. All campaigns remain in the raw table. Failures on an already-unsafe clean subject are not attributed to fuzzing. First violation is capped at 9 when no violation occurs in 8 queries. Exact discordance tests and case-cluster bootstrap intervals over represented cases are exploratory, not broad generalization.','','## Boundaries','','The action menu is finite and syntax-constrained; agents choose among four fully specified tool actions rather than generating arbitrary tool arguments. This improves auditability but restricts external validity. Four development instances are separate from five evaluation instances; several security families and all operators are shared. Only one unchanged public tool is executed on an adapted fixture; this is not a full tau-bench benchmark run. Two Qwen sizes are one family; SmolLM2 is the second. All three roles within each workflow share one model. Manually authored policies and cases are not automatically mined. The ideal guarded_counterfactual field is an oracle filter by construction, not an independently evaluated defense. Original pilot and infrastructure-aborted traces are excluded from primary statistics.']
 (ROOT/'results/RESULTS.md').write_text('\n'.join(lines)+'\n')

 print(json.dumps({'completed':report['models_complete'],'logical_episodes':report['total_logical_episodes'],'actual_inferences':report['actual_unique_inferences'],'methods':summaries},indent=2))
if __name__=='__main__':main()
