"""Run inside the image to verify the exact runtime, without external API calls."""
import subprocess,sys,time,json,urllib.request,urllib.error,os
p=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            health=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=1))
            break
        except urllib.error.URLError: time.sleep(.1)
    else: raise RuntimeError('Server did not start')
    assert health=={'status':'ok'}
    assert urllib.request.urlopen('http://127.0.0.1:8000/').status==200
    assert os.getuid()!=0
    assert not os.path.exists('/app/.env')
    try: urllib.request.urlopen('http://127.0.0.1:8000/api/search?q=pizza')
    except urllib.error.HTTPError as e: assert e.code==503
    else: raise AssertionError('Missing key should not return results')
    print('PASS: container health, homepage, non-root runtime, secret exclusion and missing-key response')
finally:
    p.terminate();p.wait(timeout=5)
