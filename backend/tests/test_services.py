import asyncio
import httpx
import pytest
from backend.app.services import places

def test_normalization_handles_optional_missing_fields():
    p=places.normalize({'id':'fixture_id','location':{'latitude':52.5,'longitude':13.4}})
    assert p['rating'] is None and p['open_now'] is None
    assert places.in_berlin(p)
    assert not places.in_berlin({'lat':48.8,'lon':2.3})

def test_provider_error_does_not_leak_secrets(monkeypatch):
    monkeypatch.setenv('GOOGLE_PLACES_API_KEY','secret-fixture')
    class Client:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def request(self,*args,**kwargs):
            return httpx.Response(403,request=httpx.Request('GET','https://places.googleapis.com'))
    monkeypatch.setattr(httpx,'AsyncClient',Client)
    with pytest.raises(places.ServiceError) as e: asyncio.run(places.search('pizza'))
    assert 'secret-fixture' not in e.value.message
    assert e.value.status==503
