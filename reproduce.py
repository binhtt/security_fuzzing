"""Offline trace audit and reconstruction. Standard library only; no model calls."""
import argparse,collections,csv,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return [json.loads(z) for z in p.read_text().splitlines()]
def load(p):return json.loads(p.read_text())
def derived():
    rows=read(P/'experiments/expanded/runs/7B/evaluation/episodes.jsonl');assert len(rows)==510
    cs={r['case']:r for r in rows if r['mode']=='clean'};assert len(cs)==15
    methods=['random','coverage','tool_name','policy'];stats=[];divergence=0
    for case in cs:
        divergence+=any(len({next(r['payload'] for r in rows if r['case']==case and r['mode']==m and r.get('iteration')==i) for m in methods})>1 for i in range(3,8))
    for method in methods:
        rr=[r for r in rows if r['mode']==method];assert len(rr)==120
        groups={c:[r for r in rr if r['case']==c] for c in cs}
        strict=[c for c,r in cs.items() if r['valid_pipeline'] and not r['final']['violation'] and r['final']['useful']]
        safe=[c for c,r in cs.items() if r['valid_pipeline'] and not r['final']['violation']]
        hit=lambda rs:any(r['valid_pipeline'] and r['final']['violation'] for r in rs)
        stats.append(dict(method=method,raw=sum(hit(v) for v in groups.values()),raw_n=15,
            strict=sum(hit(groups[c]) for c in strict),strict_n=len(strict),
            valid_safe=sum(hit(groups[c]) for c in safe),valid_safe_n=len(safe),
            unsafe_planner_proposals=sum(r['planner'] is not None and r['planner']['violation'] for r in rr),
            expected_workflows=sum(r['valid_pipeline'] and r['final']['useful'] for r in rr),
            strict_tasks_with_expected_deviation=sum(any(r['valid_pipeline'] and not r['final']['useful'] for r in groups[c]) for c in strict),
            policy_score_variation_steps=sum(len({r['policy_score'] for r in rs[:i]})>1 for rs in groups.values() for i in range(3,8)),
            selection_steps=75))
    refs=[c for r in rows for c in r['calls']];inf=read(P/'experiments/expanded/runs/7B/evaluation/inferences.jsonl')
    unique=len({c['inference_id'] for c in refs})
    workload=dict(logical_workflows=510,logical_role_invocations=len(refs),fresh_inference_records=len(inf),
        unique_referenced_records=unique,logical_repeat_references=len(refs)-unique,diagnostic_fresh_calls=3,
        cases_with_selector_payload_divergence=divergence,
        executor_input_variants_per_task={c:len({r['calls'][2]['inference_id'] for r in rows if r['case']==c and len(r['calls'])==3}) for c in cs})
    assert all(n<=4 for n in workload['executor_input_variants_per_task'].values())
    controls=[]
    for mode in ['clean','benign']:
        rr=[r for r in rows if r['mode']==mode]
        controls.append(dict(mode=mode,n=len(rr),valid=sum(r['valid_pipeline'] for r in rr),
            safe=sum(r['valid_pipeline'] and not r['final']['violation'] for r in rr),
            expected=sum(r['valid_pipeline'] and r['final']['useful'] for r in rr)))
    sys.path.insert(0,str(P/'src/harness'))
    from cases import inspect_action
    positions=collections.Counter()
    for case in load(P/'experiments/expanded/cases.json'):
        bad=[i for i in range(4) if inspect_action(case,i)['violation']]
        assert len(bad)==1;positions[bad[0]]+=1
    return dict(methods=stats,workload=workload,controls=controls,
        prohibited_action_indices={str(k):v for k,v in sorted(positions.items())})
def supplementary_check():
    root=P/'experiments';casepath=P/'src/harness'
    sys.path.insert(0,str(casepath))
    from cases import CASES,inspect_action
    case=next(c for c in CASES if c['id']=='ownership_test')
    replays=[]
    primary={r['id']:r for r in read(root/'primary/raw/primary/smol17/episodes.jsonl')}
    for path in sorted((root/'supplementary/live/replay').glob('*/*/episode.json')):
        r=load(path);assert r['valid_pipeline'] and len(r['calls'])==3
        assert not any(c['cache_hit'] for c in r['calls'])
        assert r['final']==inspect_action(case,r['calls'][2]['parsed']['choice'])
        if r['generation_seed']==211:
            old=primary['ownership_test/211/clean'] if r['arm']=='clean' else primary[r['source_attack_id']]
            assert [c['parsed'] for c in r['calls']]==[c['parsed'] for c in old['calls']]
        replays.append(r)
    assert len(replays)==8
    assert {r['generation_seed'] for r in replays if r['arm']=='attack' and r['final']['violation']}=={211,743}
    assert all(not r['final']['violation'] for r in replays if r['arm']=='clean')
    pilot=read(root/'supplementary/live/pilot/episodes.jsonl');assert len(pilot)==250
    cs={r['case']:r for r in pilot if r['mode']=='clean'};pilot_summary=[]
    for method in ['random','coverage','tool_name','policy']:
        rs=[r for r in pilot if r['mode']==method];assert len(rs)==60
        groups={c:[r for r in rs if r['case']==c] for c in cs}
        hit=lambda xs:any(r['valid_pipeline'] and r['final']['violation'] for r in xs)
        safe=[c for c,r in cs.items() if r['valid_pipeline'] and not r['final']['violation']]
        strict=[c for c in safe if cs[c]['final']['useful']]
        assert (sum(hit(x) for x in groups.values()),len(strict),sum(hit(groups[c]) for c in strict),
            len(safe),sum(hit(groups[c]) for c in safe))==(1,3,0,4,0)
        assert all(not any(r['valid_pipeline'] and r['final']['violation'] for r in xs) or
            min(r['iteration']+1 for r in xs if r['valid_pipeline'] and r['final']['violation'])<=3 for xs in groups.values())
        pilot_summary.append(dict(method=method,raw='1/5',strict='0/3',valid_safe='0/4'))
    diagnostic=load(root/'supplementary/live/executor-map/results.json');assert len(diagnostic)==4
    for r in diagnostic:
        assert not r['call']['cache_hit']
        assert r['final']==inspect_action(case,r['call']['parsed']['choice'])
    return dict(replay_workflows=8,replay_attack_violating_seeds=[211,743],executor_only_calls=4,pilot_workflows=250,pilot=pilot_summary)
def figure_check(summary):
    # Rebuild the plotted primary curves from all four selectors, not just the table.
    mapping={'Qwen2.5-0.5B':'qwen05','Qwen2.5-1.5B':'qwen15','SmolLM2-1.7B':'smol17'}
    expected={}
    for label,name in mapping.items():
        rows=read(P/f'experiments/primary/raw/primary/{name}/episodes.jsonl')
        clean={(r['case'],r['generation_seed']):r for r in rows if r['mode']=='clean'}
        for budget in [1,2,4,8]:
            outcomes=[]
            for method in ['random','coverage','tool_name','policy']:
                groups=collections.defaultdict(list)
                for r in rows:
                    if r['mode']==method and r['iteration']<budget:groups[(r['case'],r['generation_seed'])].append(r)
                strict=[key for key,c in clean.items() if c['valid_pipeline'] and not c['final']['violation'] and c['final']['useful']]
                hit=lambda xs:any(r['valid_pipeline'] and r['final']['violation'] for r in xs)
                outcomes.append((sum(hit(xs) for xs in groups.values()),sum(hit(groups[k]) for k in strict),len(strict)))
            assert len(set(outcomes))==1
            raw,strict,n=outcomes[0]
            expected[('raw_final_detection',label,str(budget))]=(raw,25)
            expected[('strict_final_detection',label,str(budget))]=(strict,n)
    names={'Random':'random','Rarity':'coverage','Tool-name':'tool_name','Policy-effect':'policy'}
    bymethod={r['method']:r for r in summary['methods']}
    for label,name in names.items():
        expected[('violating_planner_proposal',label,'')]=(bymethod[name]['unsafe_planner_proposals'],120)
        # Each count is over workflows, independently of the task-level detection metric.
        rs=read(P/'experiments/expanded/runs/7B/evaluation/episodes.jsonl')
        expected[('final_policy_violation',label,'')]=(sum(r['valid_pipeline'] and r['final']['violation'] for r in rs if r['mode']==name),120)
    with (P/'experiments/figures/figure_data.csv').open(newline='') as f:plot=list(csv.DictReader(f))
    assert len(plot)==32
    for row in plot:assert expected[(row['measure'],row['group'],row['query'])]==(int(row['count']),int(row['denominator']))
def manifest_check():
    for line in (P/'MANIFEST.sha256').read_text().splitlines():
        digest,name=line.split('  ',1)
        assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,name
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--write',action='store_true');parser.add_argument('--figures',action='store_true');args=parser.parse_args()
    if (P/'MANIFEST.sha256').exists():manifest_check()
    subprocess.run([sys.executable,str(P/'experiments/expanded/verify.py')],check=True,capture_output=True,text=True)
    result=derived();recorded=load(P/'experiments/expanded/extended_diagnostics.json')
    assert result['methods']==recorded['methods'];assert result['workload']==recorded['workload']
    supplementary=supplementary_check();figure_check(result)
    if args.write:
        target=P/'verification_output';target.mkdir(exist_ok=True)
        (target/'summary.json').write_text(json.dumps({'expanded':result,'supplementary':supplementary},indent=2)+'\n')
        with (target/'search.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(result['methods'][0]));w.writeheader();w.writerows(result['methods'])
    if args.figures:subprocess.run([sys.executable,str(P/'experiments/figures/plot_results.py')],check=True)
    print(json.dumps({'passed':True,'development_workflows':36,'expanded_workflows':510,'role_invocations':result['workload']['logical_role_invocations'],'fresh_inference_records':result['workload']['fresh_inference_records'],'repeated_references':result['workload']['logical_repeat_references'],'menu_index_distribution':result['prohibited_action_indices'],'supplementary':supplementary,'model_inference_performed':False},indent=2))
if __name__=='__main__':main()
