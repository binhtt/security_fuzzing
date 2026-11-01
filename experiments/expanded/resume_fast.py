"""8-thread resumption with native single-prefix reuse and archived role checks."""
import inspect,json,sys,textwrap,time
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'source/security-fuzzing/src/harness'))
import study as s
source=textwrap.dedent(inspect.getsource(s.Backend.call)).replace('self.llm.reset();start=time.perf_counter()','start=time.perf_counter()')
namespace=dict(s.__dict__);exec(compile(source,str(P/'resume_fast.py'),'exec'),namespace);s.Backend.call=namespace['call']
original=s.Backend.__init__
def init(self,path,out,threads=8):
    original(self,path,out,8)
    target=out/'recovery-replay-checks.json'
    if target.exists():return
    checks=[]
    for role in ['reader','planner','executor']:
        x=next(v for v in self.cache.values() if v['role']==role)
        prompt=f"<|im_start|>system\n{x['system']}<|im_end|>\n<|im_start|>user\n{x['user']}<|im_end|>\n<|im_start|>assistant\n"
        result=self.llm(prompt,max_tokens=56 if role=='reader' else 16,temperature=.7,top_p=.9,seed=x['seed'],grammar=self.grammars['reader' if role=='reader' else 'decision'],stop=['<|im_end|>'])
        raw=result['choices'][0]['text'];parsed=json.loads(raw)
        checks.append({'role':role,'reference_id':x['id'],'raw':raw,'parsed':parsed,'matches':parsed==x['parsed'],'usage':result['usage']})
    target.write_text(json.dumps({'diagnostic_fresh_calls':3,'checks':checks,'all_match':all(x['matches'] for x in checks)},indent=2))
    assert all(x['matches'] for x in checks)
s.Backend.__init__=init
import run
run.main()
