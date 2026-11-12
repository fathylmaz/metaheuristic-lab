"""Pure stdlib checks for the v2.9 local-only deployment contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_web_container_serves_production_bundle():
    dockerfile = (ROOT/'frontend/Dockerfile').read_text()
    assert 'RUN npm run build' in dockerfile
    assert 'COPY --from=builder /app/dist' in dockerfile
    assert 'nginx:' in dockerfile
    assert 'npm run dev' not in dockerfile


def test_api_has_no_published_host_port():
    compose = (ROOT/'docker-compose.yml').read_text()
    assert '127.0.0.1:5173:80' in compose
    assert '127.0.0.1:8000:8000' not in compose
    assert './backend/data:/app/data' in compose
    assert 'condition: service_healthy' in compose


def test_nginx_proxies_api_and_local_docs():
    nginx = (ROOT/'frontend/nginx.conf').read_text()
    assert 'location /api/' in nginx
    assert 'proxy_pass http://api:8000;' in nginx
    assert 'location = /docs' in nginx
    assert 'try_files $uri $uri/ /index.html;' in nginx


def test_backup_script_and_docs_present():
    assert (ROOT/'scripts/backup_experiments.py').is_file()
    assert (ROOT/'scripts/verify_docker_windows.ps1').is_file()
    assert (ROOT/'docs/DEPLOY_LOCAL.md').is_file()


def test_docker_excludes_local_database_from_build_context():
    assert 'data' in (ROOT/'backend/.dockerignore').read_text().splitlines()
    assert 'node_modules' in (ROOT/'frontend/.dockerignore').read_text().splitlines()
