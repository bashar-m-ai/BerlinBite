"""Interactive local setup: hidden input, no secrets in command history or stdout."""
from pathlib import Path
from getpass import getpass
import os
root=Path(__file__).resolve().parents[1]
target=root/'.env'
values={}
if target.exists():
    for line in target.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);values[k]=v
for key,label in [('GOOGLE_PLACES_API_KEY','Google Places key'),('OPENAI_API_KEY','OpenAI key')]:
    value=getpass(label+' (hidden; Enter keeps current): ').strip()
    if value:
        if '\n' in value or '\r' in value or any(c in value for c in '\"\''):
            raise SystemExit('Unexpected characters in key. Nothing saved.')
        values[key]=value
values.setdefault('OPENAI_MODEL','gpt-4.1-mini')
values.setdefault('MAX_REQUESTS_PER_MINUTE','20')
fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
os.chmod(target,0o600)
with os.fdopen(fd,'w') as f:
    f.write('\n'.join(k+'='+v for k,v in values.items())+'\n')
print('Keys saved privately in .env. Restart the app to use them.')
