from pathlib import Path
import json,hashlib,copy,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/harness'))
from cases import CASES,inspect_action
case=next(c for c in CASES if c['id']=='privacy_test')
base=ROOT/'results/raw/diagnostics'
fmt=json.loads((base/'format_sanity/summary.json').read_text())
menu=json.loads((base/'menu_diagnostic/summary.json').read_text())
records=[]
for model in ['qwen05','qwen15','smol17']:
    sha=json.loads((ROOT/'results/raw/primary'/model/'manifest.json').read_text())['model_sha256']
    for folder in ['format_sanity','menu_diagnostic']:
        inf=[json.loads(l) for l in (base/folder/model/'inferences.jsonl').read_text().splitlines()]
        byid={r['id']:r for r in inf}
        assert len(byid)==len(inf)==len({r['key'] for r in inf})
        for r in inf:
            assert json.loads(r['raw'])==r['parsed'] and r['usage']['completion_tokens']>0
            prompt=f"<|im_start|>system\n{r['system']}<|im_end|>\n<|im_start|>user\n{r['user']}<|im_end|>\n<|im_start|>assistant\n"
            key=hashlib.sha256(json.dumps([sha,prompt,r['seed'],r['role'],.7,.9,56 if r['role']=='reader' else 16],ensure_ascii=False).encode()).hexdigest()
            assert key==r['key']
        if folder=='format_sanity':
            f=next(x for x in fmt if x['model']==model)
            assert f['correct']==4 and len(inf)==4
            for row in f['rows']:assert byid[row['inference_id']]['parsed']=={'choice':row['expected']}
        else:
            eps=[json.loads(l) for l in (base/folder/model/'episodes.jsonl').read_text().splitlines()]
            assert len(eps)==4 and len(inf)==9
            for r in eps:
                c=copy.deepcopy(case);k=r['rotation'];c['actions']=c['actions'][k:]+c['actions'][:k]
                assert c['actions']==r['action_menu']
                for idx,call in enumerate(r['calls']):
                    assert call['parsed']==byid[call['inference_id']]['parsed']
                    assert byid[call['inference_id']]['seed']==631+1000*idx
                assert inspect_action(c,r['calls'][-1]['parsed']['choice'])==r['final']
            m=next(x for x in menu if x['model']==model)
            assert sum(e['final']['violation'] for e in eps)==m['unsafe']
            assert m['protocol_sha256']==hashlib.sha256((ROOT/'configs/menu_diagnostic_protocol.json').read_bytes()).hexdigest()
    records.append({'model':model,'format_calls':4,'menu_calls':9,'status':'passed'})
for m in json.loads((ROOT/'configs/model_sources.json').read_text()):
    assert m['sha256']==json.loads((ROOT/'results/raw/primary'/m['model']/'manifest.json').read_text())['model_sha256']
result={'models':records,'additional_fresh_inferences':39,'excluded_from_primary':True,'model_source_hashes':'passed'}
(ROOT/'validation/diagnostic_verification.json').write_text(json.dumps(result,indent=2))
print('Diagnostic evidence checks passed; no model inference performed.')
