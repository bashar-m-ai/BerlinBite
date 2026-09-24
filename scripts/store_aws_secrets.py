"""Run only after approving deployment and creating the secret containers with Terraform."""
import subprocess,json,tempfile,os
from getpass import getpass
for name,label in [('berlinbite/google-places','Google Places key'),('berlinbite/openai','OpenAI key')]:
    value=getpass(label+' (hidden): ').strip()
    if not value: raise SystemExit('A key is required; remaining secrets were not updated.')
    fd,path=tempfile.mkstemp(prefix='berlinbite-secret-',suffix='.json')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump({'SecretId':name,'SecretString':value},f)
        result=subprocess.run(['aws','secretsmanager','put-secret-value','--profile','berlinbite','--region','eu-central-1','--cli-input-json','file://'+path,'--query','VersionId','--output','text'],text=True,capture_output=True)
    finally:
        os.unlink(path)
    if result.returncode: raise SystemExit('AWS rejected the secret update. Check permissions and secret existence; no key was printed.')
    print(name+': stored')
