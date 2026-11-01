"""Analyze supplemental outputs without additional model inference."""
import collections,csv,json
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
    replays=[]
    for path in sorted((P/'live/replay').glob('*/*/episode.json')):
        r=json.loads(path.read_text());replays.append(dict(seed=r['generation_seed'],arm=r['arm'],valid=r['valid_pipeline'],violation=r['final']['violation'],expected=r['final']['useful'],planner=r['planner']['action'] if r['planner'] else None,final=r['final']['action'],fresh_calls=sum(not c['cache_hit'] for c in r['calls'])))
    rows=[json.loads(x) for x in (P/'live/pilot/episodes.jsonl').read_text().splitlines()]
    assert len(replays)==8, 'Fresh replay is incomplete'
    assert len(rows)==250, 'Pilot is incomplete'
    controls={r['case']:r for r in rows if r['mode']=='clean'}
    stats=[]
    for method in ['random','coverage','tool_name','policy']:
        rr=[r for r in rows if r['mode']==method];groups=collections.defaultdict(list)
        for r in rr:groups[r['case']].append(r)
        raw=strict=safe=eligible_strict=eligible_safe=late=0
        first=[]
        for case,rs in groups.items():
            hits=[r['iteration']+1 for r in rs if r['valid_pipeline'] and r['final']['violation']]
            c=controls[case];ok=c['valid_pipeline'] and not c['final']['violation'];proper=ok and c['final']['useful']
            eligible_safe+=ok;eligible_strict+=proper
            raw+=bool(hits);safe+=ok and bool(hits);strict+=proper and bool(hits)
            late+=bool(hits) and min(hits)>3
            first.append(min(hits) if hits else 13)
        stats.append(dict(method=method,cases=len(groups),raw_detected=raw,strict_detected=strict,strict_eligible=eligible_strict,valid_safe_detected=safe,valid_safe_eligible=eligible_safe,first_detection_after_initialization=late,valid_workflows=sum(r['valid_pipeline'] for r in rr),adversarial_workflows=len(rr),unique_payloads=len({(r['case'],r['payload']) for r in rr}),mean_capped_first_detection=sum(first)/len(first)))
    divergence=[]
    for i in range(12):
        q=[r for r in rows if r['mode'] in ['random','coverage','tool_name','policy'] and r['iteration']==i]
        groups=collections.defaultdict(list)
        for r in q:groups[r['case']].append(r)
        divergence.append(dict(query=i+1,case_groups=len(groups),different_payload_groups=sum(len({r['payload'] for r in rs})>1 for rs in groups.values())))
    manifest=json.loads((P/'live/pilot/manifest.json').read_text())
    executor_map=json.loads((P/'live/executor-map/results.json').read_text())
    assert len(executor_map)==4
    assert all(not r['call']['cache_hit'] for r in executor_map)
    assert all(r['fresh_calls']==3 for r in replays)
    assert all(s['adversarial_workflows']==60 for s in stats)
    summary={'replay':replays,'pilot':stats,'divergence':divergence,'executor_map':executor_map,'pilot_manifest':manifest,'new_workflows':258,'additional_executor_only_calls':4,'scope':'Exploratory pilot on five cases and one seed; no independent-task generalization; historical and new detection rates must not be pooled.'}
    (P/'new_results.json').write_text(json.dumps(summary,indent=2))
    with (P/'pilot_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
    with (P/'replay_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(replays[0]));w.writeheader();w.writerows(replays)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
