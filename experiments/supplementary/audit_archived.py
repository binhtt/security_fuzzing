"""Additional descriptive trace analysis; no new inference or independent observations."""
import collections,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=[]
    for model in ['qwen05','qwen15','smol17']:
        d=ROOT/'results/raw/primary'/model
        rows=[json.loads(x) for x in (d/'episodes.jsonl').read_text().splitlines()]
        valid=[r for r in rows if r['mode'] in ['random','coverage','tool_name','policy'] and r['valid_pipeline']]
        groups=collections.defaultdict(list)
        for r in rows:
            if r['mode'] in ['random','coverage','tool_name','policy']:
                groups[(r['case'],r['generation_seed'],r['iteration'])].append(r)
        inf=[json.loads(x) for x in (d/'inferences.jsonl').read_text().splitlines()]
        out.append({'model':model,'valid_adversarial':len(valid),'planner_unsafe_executor_safe':sum(r['planner']['violation'] and not r['final']['violation'] for r in valid),'planner_safe_executor_unsafe':sum(not r['planner']['violation'] and r['final']['violation'] for r in valid),'both_unsafe':sum(r['planner']['violation'] and r['final']['violation'] for r in valid),'unique_executor_inferences':len({r['key'] for r in inf if r['role']=='executor'}),'shared_payload_groups_by_query':{i:sum(len({r['payload'] for r in rs})==1 for k,rs in groups.items() if k[2]==i) for i in range(8)},'divergent_payload_groups_by_query':{i:sum(len({r['payload'] for r in rs})>1 for k,rs in groups.items() if k[2]==i) for i in range(8)}})
    (ROOT/'supplementary/archived_analysis.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
