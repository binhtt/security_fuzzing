"""Post-hoc cohort sensitivity; derived observations only, no new model calls."""
from pathlib import Path
import json,collections,csv
ROOT=Path(__file__).resolve().parents[2]
METHODS=['random','coverage','tool_name','policy']
def main():
 output=[]
 for model in ['qwen05','qwen15','smol17']:
  base=ROOT/'results'/'raw'/'primary'/model
  if not (base/'manifest.json').exists():continue
  rows=[json.loads(l) for l in (base/'episodes.jsonl').read_text().splitlines()]
  control={(r['case'],r['generation_seed']):r for r in rows if r['mode']=='clean'}
  groups=collections.defaultdict(list)
  for r in rows:
   if r['mode'] in METHODS:groups[(r['case'],r['generation_seed'],r['mode'])].append(r)
  for method in METHODS:
   for stratum in ['all','valid_safe','valid_safe_expected']:
    selected=[]
    for (case,seed,m),rr in groups.items():
     if m!=method:continue
     c=control[(case,seed)]
     eligible=stratum=='all' or (c['valid_pipeline'] and not c['final']['violation'] and (stratum=='valid_safe' or c['final']['useful']))
     if eligible:selected.append(rr)
    output.append({'model':model,'method':method,'stratum':stratum,'campaigns':len(selected),'detected':sum(any(r['final']['violation'] for r in rr) for rr in selected),'case_clusters':len({rr[0]['case'] for rr in selected}),'note':'Post-hoc sensitivity to expected-action proxy; excluded from predefined primary comparisons.'})
 with (ROOT/'results/processed/control_sensitivity.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
 (ROOT/'results/processed/control_sensitivity.json').write_text(json.dumps(output,indent=2))
 print(json.dumps([r for r in output if r['stratum']=='valid_safe'],indent=2))
if __name__=='__main__':main()
