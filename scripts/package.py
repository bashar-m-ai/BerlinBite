"""Package tracked source only; excluded secrets never enter the submission archive."""
from pathlib import Path
import subprocess,zipfile
root=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
output=root.parent/'BerlinBite-development-package.zip'
prefix='BerlinBite-development/'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for rel in files:
        if not rel: continue
        p=root/rel
        if not p.is_file(): continue
        if p.name=='.env' or '.venv' in p.parts or '.terraform' in p.parts or '.tfstate' in p.name or p.suffix=='.tfplan':
            raise RuntimeError('Private file unexpectedly tracked: '+rel)
        if rel.startswith('docs/Phase-1'): dest='02-Conception-Phase/'+p.name
        elif rel.startswith('docs/Phase-2'): dest='03-Development-Phase/'+p.name
        elif rel.startswith('docs/Phase-3'): dest='04-Final-Phase/'+p.name
        elif rel.startswith('docs/'): dest='01-Research-and-Development/'+p.name
        else: dest='04-Final-Phase/BerlinBite/'+rel
        source_dest='04-Final-Phase/BerlinBite/'+rel
        z.write(p,prefix+source_dest)
        if dest!=source_dest: z.write(p,prefix+dest)
    z.writestr(prefix+'README-FIRST.txt','DEVELOPMENT DRAFT. Live API testing, visual review and AWS deployment are pending. Read VALIDATION.md before submission. The source folder needs a private .env configured using scripts/configure_keys.py. No keys are included. The complete source directory includes its documentation.\n')
print(output)
