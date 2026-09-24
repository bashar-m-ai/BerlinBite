"""Run only after approving deployment and creating the secret containers with Terraform."""
import subprocess,json
from getpass import getpass
for name,label in [('berlinbite/google-places','Google Places key'),('berlinbite/openai','OpenAI key')]:
    value=getpass(label+' (hidden): ').strip()
    if not value: raise SystemExit('A key is required; remaining secrets were not updated.')
    result=subprocess.run(['aws','secretsmanager','put-secret-value','--profile','berlinbite','--region','eu-central-1','--cli-input-json','file:///dev/stdin','--query','VersionId','--output','text'],input=json.dumps({'SecretId':name,'SecretString':value}),text=True,capture_output=True)
    if result.returncode: raise SystemExit('AWS rejected the secret update. Check permissions and secret existence; no key was printed.')
    print(name+': stored')
