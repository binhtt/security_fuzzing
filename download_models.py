"""Download the exact larger-model weights and check published LFS SHA256."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while chunk:=f.read(8*1024*1024):h.update(chunk)
    return h.hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--models',nargs='+',choices=['3B','7B'],default=['3B','7B']);args=ap.parse_args()
(ROOT/'models').mkdir(exist_ok=True)
for size in args.models:
    for row in json.loads((ROOT/f'model-{size}.json').read_text()):
        path=ROOT/'models'/row['path'];expected=row['lfs']['oid']
        if path.exists():
            assert digest(path)==expected,'Existing weights do not match expected hash'
            continue
        temp=path.with_suffix('.download')
        url=f'https://huggingface.co/Qwen/Qwen2.5-{size}-Instruct-GGUF/resolve/main/'+row['path']
        with urllib.request.urlopen(url,timeout=120) as r,temp.open('wb') as out:
            while block:=r.read(8*1024*1024):out.write(block)
        assert digest(temp)==expected,'Download hash mismatch; not installed'
        temp.replace(path)
        print('Verified',path.name,flush=True)
