"""Offline release and accessibility contracts, no JS runtime needed."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_all_research_labs_are_lazy_loaded():
    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    for module in ("ComparisonLab", "BenchmarkSuite", "SensitivityLab", "DimensionalLab", "ReportsLab", "JobsLab", "ScienceLab", "AcoLab", "Landscape"):
        assert f"lazy(() => import('./components/{module}'))" in app
        assert f"import {module} from './components/{module}'" not in app
    assert 'Suspense fallback={<ModuleLoading/>}' in app
    assert 'ModuleErrorBoundary' in app


def test_keyboard_navigation_and_accessible_loading():
    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    css = (ROOT / "frontend/src/styles.css").read_text(encoding="utf-8")
    assert 'aria-controls="lab-sidebar"' in app
    assert 'aria-expanded={sidebarOpen}' in app
    assert "event.key === 'Escape'" in app
    assert 'href="#main-content"' in app
    assert 'role="status" aria-live="polite"' in app
    assert ':focus-visible' in css
    assert 'prefers-reduced-motion:reduce' in css


def test_version_and_wasm_provider_remain_consistent():
    import json
    package = json.loads((ROOT / 'frontend/package.json').read_text(encoding='utf-8'))
    app = (ROOT / 'frontend/src/App.tsx').read_text(encoding='utf-8')
    api = (ROOT / 'backend/app/main.py').read_text(encoding='utf-8')
    assert package['version'] == '3.0.0'
    assert 'BUILD {APP_VERSION}' in app
    assert 'LAB / Sürüm {APP_VERSION}' in app
    assert 'v{APP_VERSION}' in app
    assert "import { version as APP_VERSION } from '../package.json'" in app
    assert 'Sürüm 2.10' not in app
    assert "version='3.0.0'" in api
    assert package['devDependencies']['rollup'].startswith('npm:@rollup/wasm-node@')
    assert package['overrides']['rollup'] == '$rollup'
    assert package['scripts']['report:bundle'].endswith('bundle_report.mjs')
    assert (ROOT / 'frontend/scripts/bundle_report.mjs').is_file()


def test_two_new_browser_regressions_present():
    spec = (ROOT / 'frontend/e2e/lab-smoke.spec.ts').read_text(encoding='utf-8')
    assert 'mobil menü klavyeyle kapanır' in spec
    assert 'yalnızca açılan laboratuvar yüklenir' in spec
