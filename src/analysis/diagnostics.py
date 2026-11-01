"""Menu-index and handoff diagnostics; observational, not a causal bias test."""
from pathlib import Path
import json,csv,collections
ROOT=Path(__file__).resolve().parents[2]
def main():
    output=[]
    for model in ['qwen05','qwen15','smol17']:
        base=ROOT/'results'/'raw'/'primary'/model
        if not (base/'manifest.json').exists():continue
        groups=collections.defaultdict(list)
        for line in (base/'episodes.jsonl').read_text().splitlines():
            r=json.loads(line);groups[(r['case'],r['mode'])].append(r)
        for (case,mode),rr in groups.items():
            indices=collections.Counter();transitions=collections.Counter()
            for r in rr:
                if not r['valid_pipeline']:transitions['invalid']+=1;continue
                indices[r['calls'][-1]['parsed']['choice']]+=1
                transitions[('unsafe' if r['planner']['violation'] else 'safe')+'_to_'+('unsafe' if r['final']['violation'] else 'safe')]+=1
            output.append({'model':model,'case':case,'mode':mode,'logical_episodes':len(rr),**{'executor_choice_'+str(k):indices[k] for k in range(4)},**{k:transitions[k] for k in ['safe_to_safe','safe_to_unsafe','unsafe_to_safe','unsafe_to_unsafe','invalid']}})
    with (ROOT/'results/processed/diagnostics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    print('Wrote',len(output),'diagnostic rows')
if __name__=='__main__':main()
