"""Fixtures are confined to tests; the product never substitutes fabricated results."""
from fastapi.testclient import TestClient
from backend.app.main import app, hits
from backend.app.services import places
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def client(monkeypatch):
    hits.clear()
    monkeypatch.setenv('GOOGLE_PLACES_API_KEY','')
    return TestClient(app)

def test_missing_key_is_explicit(client):
    r=client.get('/api/search?q=pizza')
    assert r.status_code==503
    assert 'not connected' in r.json()['detail']

def test_secrets_never_exposed(client,monkeypatch):
    monkeypatch.setenv('GOOGLE_PLACES_API_KEY','test-private-secret')
    r=client.get('/api/config')
    assert r.json()['places_ready'] is True
    assert 'test-private-secret' not in r.text

def test_input_validation(client):
    assert client.get('/api/search?q=x').status_code==422
    assert client.get('/api/places/bad!id').status_code==422
    assert client.post('/api/insight',json={'place_id':'valid_id','visit_at':'2026-09-25T19:00:00'}).status_code==422

def test_search_adapter_result(client,monkeypatch):
    monkeypatch.setattr(places,'search',AsyncMock(return_value=[{'id':'fixture_id','name':'Test fixture'}]))
    r=client.get('/api/search?q=pizza')
    assert r.json()['places'][0]['id']=='fixture_id'
    assert r.headers['cache-control']=='no-store'

def test_request_limit(client):
    for _ in range(20): client.get('/api/search?q=pizza')
    assert client.get('/api/search?q=pizza').status_code==429

def test_home_and_health(client):
    assert client.get('/').status_code==200
    assert client.get('/api/health').json()=={'status':'ok'}
    assert "frame-ancestors 'none'" in client.get('/').headers['content-security-policy']

def test_insight_degrades_without_ai_or_weather(client,monkeypatch):
    from datetime import datetime,timedelta,timezone
    from backend.app.services import ai,weather
    fixture={'id':'fixture_id','name':'Test fixture','lat':52.5,'lon':13.4,'summary':None}
    monkeypatch.setattr(places,'details',AsyncMock(return_value=fixture))
    monkeypatch.setattr(ai,'advice',AsyncMock(return_value=None))
    monkeypatch.setattr(weather,'current',AsyncMock(return_value=None))
    visit=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    r=client.post('/api/insight',json={'place_id':'fixture_id','visit_at':visit})
    assert r.status_code==200
    data=r.json()
    assert data['weather'] is None
    assert data['advice_source']=='General dining guidance'
    assert 'Not verified' in data['english']
    assert 'not live occupancy' in data['crowd']['disclaimer']
