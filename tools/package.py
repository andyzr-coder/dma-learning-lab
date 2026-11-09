"""Create reproducible source and runnable-offline bundles without private research."""
from pathlib import Path
import zipfile,shutil
root=Path(__file__).resolve().parents[1]
target=root/'public/downloads';target.mkdir(parents=True,exist_ok=True)
private={'github_private.py','extract_sources.py','build-source-registry.py','write_synthesis.py','build_testing_content.py','audit-doc-source.py'}
def allowed(p):
    return p.is_file() and p.name not in private and p.suffix not in {'.zip','.log','.pyc'} and (p.suffix not in {'.png','.jpg'} or 'figures' in p.parts) and '__pycache__' not in p.parts and 'pdf-review' not in p.parts and 'figure-review' not in p.parts
files=[]
for folder in ['src','content','tools','tests','public','qa']:
    files.extend(p for p in (root/folder).rglob('*') if allowed(p))
files.extend(root/p for p in ['README.md','package.json','package-lock.json','.gitignore','.gitattributes'])
with zipfile.ZipFile(target/'dma-learning-lab-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(target/'dma-offline-website.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((root/'dist').rglob('*')):
        if p.is_file() and '.git' not in p.parts and p.suffix!='.zip':z.write(p,p.relative_to(root).as_posix())
    z.write(root/'tools/serve.mjs','tools/serve.mjs')
    z.writestr('START-HERE.txt','DMA offline website\n1. Install Node.js 22+ if needed.\n2. Open this extracted folder in a terminal.\n3. Run: node tools/serve.mjs\n4. Open http://127.0.0.1:4174/\nFor reading only, double-click dist/downloads/dma-handbook.html.\n')
for p in target.glob('*.zip'):
    shutil.copy2(p,root/'dist/downloads'/p.name)
    print(p.name,p.stat().st_size)
