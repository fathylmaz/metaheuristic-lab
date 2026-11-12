"""Final release contracts: metadata, CI, docs and source-only screenshot tooling."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from release_audit import checks  # noqa: E402


def test_v300_api_and_frontend_version():
    from fastapi.testclient import TestClient
    from app.main import app
    assert json.loads((ROOT/'frontend/package.json').read_text())['version']=='3.0.0'
    with TestClient(app) as client:
        assert client.get('/api/health').json() == {'status':'ok','version':'3.0.0'}
        assert client.get('/openapi.json').json()['info']['version']=='3.0.0'


def test_release_audit_clean():
    assert checks(ROOT) == []


def test_ci_health_version_is_dynamic():
    ci = (ROOT/'.github/workflows/ci.yml').read_text(encoding='utf-8')
    assert "Path('frontend/package.json')" in ci
    assert "actual.get('version') != expected" in ci
    assert '"version":"2.9.0"' not in ci


def test_two_language_entry_points():
    for name in ('README.md','README_EN.md','README_TR.md'):
        text=(ROOT/name).read_text(encoding='utf-8')
        assert 'Metaheuristic Lab' in text
        assert 'README_TR.md' in text or name=='README_TR.md'
        assert 'README_EN.md' in text or name=='README_EN.md'


def test_screenshot_tool_captures_real_page_without_fake_assets():
    script=(ROOT/'frontend/scripts/capture_screenshots.mjs').read_text(encoding='utf-8')
    assert 'page.goto(base' in script
    assert 'page.screenshot(' in script
    assert 'REVIEW ALL SCREENSHOTS' in script
    assert json.loads((ROOT/'frontend/package.json').read_text())['scripts']['capture:screenshots']


def test_local_only_deployment_documented():
    docker=(ROOT/'docker-compose.yml').read_text(encoding='utf-8')
    security=(ROOT/'SECURITY.md').read_text(encoding='utf-8')
    assert '127.0.0.1:5173:80' in docker
    assert 'not expose' in security.lower()


def test_academic_limits_are_explicit():
    limitations=(ROOT/'docs/RESEARCH_LIMITATIONS.md').read_text(encoding='utf-8')
    for term in ('NFE', 'ACO', 'checkpoint', 'bootstrap', 'HTTPS'):
        assert term.lower() in limitations.lower()
