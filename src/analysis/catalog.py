"""Deduplicate observed failures; preserve evidence links and clean qualification."""
from pathlib import Path
import json,collections
ROOT=Path(__file__).resolve().parents[2]
def main():
    catalog=[]
    for model in ['qwen05','qwen15','smol17']:
        base=ROOT/'results'/'raw'/'primary'/model
        if not (base/'manifest.json').exists():continue
        rows=[json.loads(l) for l in (base/'episodes.jsonl').read_text().splitlines()]
        clean={(r['case'],r['generation_seed']):r for r in rows if r['mode']=='clean'}
        groups=collections.defaultdict(list)
        for r in rows:
            if r['mode'] not in ['random','coverage','tool_name','policy'] or not r['final']['violation']:continue
            groups[r['case']].append(r)
        for case,rr in groups.items():
            qualified=[r for r in rr if clean[(case,r['generation_seed'])]['valid_pipeline'] and clean[(case,r['generation_seed'])]['final']['useful'] and not clean[(case,r['generation_seed'])]['final']['violation']]
            first=(qualified or rr)[0]
            catalog.append({'model':model,'case':case,'violating_logical_episodes':len(rr),'clean_qualified_violating_episodes':len(qualified),'distinct_payloads':len({r['payload'] for r in rr}),'distinct_seed_payloads':len({(r['generation_seed'],r['payload']) for r in rr}),'methods_observing':sorted({r['mode'] for r in rr}),'representative_episode_id':first['id'],'representative_clean_qualified':bool(qualified),'payload':first['payload'],'final_receipt':first['final'],'role_inference_ids':[c['inference_id'] for c in first['calls']],'interpretation':'One constructed policy/instance failure class; repeated episodes, seeds and methods are not independent vulnerabilities.'})
    (ROOT/'results/processed/failure_catalog.json').write_text(json.dumps(catalog,indent=2))
    print(json.dumps([{k:r[k] for k in ['model','case','violating_logical_episodes','clean_qualified_violating_episodes']} for r in catalog],indent=2))
if __name__=='__main__':main()
