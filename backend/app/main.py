"""HTTP adapter; all optimization work lives outside the web layer."""
from fastapi import FastAPI, HTTPException, Query, Request, status
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from .http_safety import ApiSafetyMiddleware
from .job_queue import JobQueue, QueueFull, JobNotFound, JobConflict
from .comparison_store import _database
from .catalog import catalog
from .reports import ReportKind, list_reports, build_report, as_markdown, as_html
from .optimizers.aco import ACORequest, ACOResponse, simulate_aco
from .comparison import ComparisonRequest, ComparisonResponse, compare
from .comparison_store import save, list_saved, load
from .benchmark_suite import BenchmarkSuiteRequest, BenchmarkSuiteResult, benchmark_suite
from .benchmark_store import save_benchmark, list_benchmarks, load_benchmark
from .sensitivity import PARAMETERS, SensitivityRequest, SensitivityResult, sensitivity
from .sensitivity_store import save_sensitivity, list_sensitivity, load_sensitivity
from .models import RunRequest, RunResponse
from .dimensional import DimensionalRequest, DimensionalResult, run_dimensional
from .dimensional_store import save_dimensional, list_dimensional, load_dimensional
from .scientific_validation import audit_dimensional
from .optimizers.firefly import simulate as simulate_firefly
from .optimizers.pso import simulate as simulate_pso
from .optimizers.cuckoo import simulate as simulate_cuckoo
from .optimizers.mfo import simulate as simulate_mfo
from .optimizers.gwo import simulate as simulate_gwo
from .optimizers.woa import simulate as simulate_woa
from .optimizers.abc import simulate as simulate_abc
from .optimizers.bat import simulate as simulate_bat
from .optimizers.ssa import simulate as simulate_ssa
from .optimizers.sma import simulate as simulate_sma
from .optimizers.iwo import simulate as simulate_iwo
from .optimizers.annealing import simulate as simulate_sa
from .optimizers.gravitational import simulate as simulate_gsa
from .optimizers.differential import simulate as simulate_de

@asynccontextmanager
async def lifespan(app: FastAPI):
    queue = JobQueue(_database())
    app.state.job_queue = queue
    queue.start()
    try:
        yield
    finally:
        queue.stop()


app = FastAPI(title='Metaheuristic Lab API', version='3.0.0',
              description='Deterministic educational metaheuristic simulations', lifespan=lifespan)
app.add_middleware(ApiSafetyMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'], allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Content-Type'])


@app.get('/api/health')
def health():
    return {'status': 'ok', 'version': '3.0.0'}


@app.get('/api/catalog')
def get_catalog():
    return catalog()


@app.post('/api/simulations', response_model=RunResponse)
def run_simulation(request: RunRequest):
    if request.algorithm == 'pso':
        return simulate_pso(request)
    if request.algorithm == 'abc':
        return simulate_abc(request)
    if request.algorithm == 'cs':
        return simulate_cuckoo(request)
    if request.algorithm == 'mfo':
        return simulate_mfo(request)
    if request.algorithm == 'gwo':
        return simulate_gwo(request)
    if request.algorithm == 'woa':
        return simulate_woa(request)
    if request.algorithm == 'ssa':
        return simulate_ssa(request)
    if request.algorithm == 'sma':
        return simulate_sma(request)
    if request.algorithm == 'de':
        return simulate_de(request)
    if request.algorithm == 'gsa':
        return simulate_gsa(request)
    if request.algorithm == 'sa':
        return simulate_sa(request)
    if request.algorithm == 'iwo':
        if request.iwo_max_population < request.population_size or request.iwo_min_seeds > request.iwo_max_seeds or request.iwo_sigma_final > request.iwo_sigma_initial:
            raise HTTPException(status_code=422, detail='IWO popülasyon, tohum veya sigma sınırları geçersiz')
        return simulate_iwo(request)
    if request.algorithm == 'ba':
        if request.ba_frequency_max < request.ba_frequency_min:
            raise HTTPException(status_code=422, detail='Maksimum frekans minimumdan küçük olamaz')
        return simulate_bat(request)
    return simulate_firefly(request)


@app.exception_handler(RequestValidationError)
async def safe_validation_errors(_request, exc: RequestValidationError):
    # Avoid serializing arbitrary non-JSON input (e.g. NaN) from error details.
    errors = [
        {'loc': [str(x) for x in item['loc']], 'msg': item['msg'], 'type': item['type']}
        for item in exc.errors()
    ]
    return JSONResponse(status_code=422, content={'detail': errors})


@app.post('/api/comparisons', response_model=ComparisonResponse)
def run_comparison(request: ComparisonRequest):
    result = compare(request)
    save(result)
    return result


@app.get('/api/comparisons')
def comparison_history():
    return {'comparisons': list_saved()}


@app.get('/api/comparisons/{comparison_id}', response_model=ComparisonResponse)
def get_comparison(comparison_id: str):
    result = load(comparison_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Deney kaydı bulunamadı')
    return result


@app.post('/api/aco/simulations', response_model=ACOResponse)
def run_aco_simulation(request: ACORequest):
    return simulate_aco(request)


@app.post('/api/benchmarks', response_model=BenchmarkSuiteResult)
def run_benchmark_suite(request: BenchmarkSuiteRequest):
    result = benchmark_suite(request)
    save_benchmark(result)
    return result


@app.get('/api/benchmarks')
def benchmark_history():
    return {'benchmarks': list_benchmarks()}


@app.get('/api/benchmarks/{benchmark_id}', response_model=BenchmarkSuiteResult)
def get_benchmark_suite(benchmark_id: str):
    result = load_benchmark(benchmark_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Benchmark kaydı bulunamadı')
    return result


@app.get('/api/sensitivity/parameters')
def sensitivity_parameters():
    return {'parameters': {name:[param.model_dump() for param in entries] for name,entries in PARAMETERS.items()}}


@app.post('/api/sensitivity',response_model=SensitivityResult)
def run_sensitivity(request:SensitivityRequest):
    result=sensitivity(request)
    save_sensitivity(result)
    return result


@app.get('/api/sensitivity')
def sensitivity_history():
    return {'studies':list_sensitivity()}


@app.get('/api/sensitivity/{sensitivity_id}',response_model=SensitivityResult)
def get_sensitivity(sensitivity_id:str):
    result=load_sensitivity(sensitivity_id)
    if result is None:
        raise HTTPException(status_code=404,detail='Parametre duyarlılığı deneyi bulunamadı')
    return result


@app.post('/api/dimensional', response_model=DimensionalResult)
def dimensional_experiment(request: DimensionalRequest):
    result = run_dimensional(request)
    save_dimensional(result)
    return result


@app.get('/api/dimensional')
def dimensional_history():
    return {'experiments': list_dimensional()}


@app.get('/api/dimensional/{experiment_id}', response_model=DimensionalResult)
def dimensional_read(experiment_id: str):
    result = load_dimensional(experiment_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Yüksek boyutlu deney kaydı bulunamadı')
    return result


@app.get('/api/science/dimensional/{experiment_id}')
def scientific_audit(experiment_id: str):
    """Read-only verification of a saved D-dimensional run and measured timings."""
    result = load_dimensional(experiment_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Bilimsel denetim için deney bulunamadı')
    return audit_dimensional(result)


@app.get('/api/reports')
def report_history():
    return {'reports': list_reports()}


@app.get('/api/reports/{kind}/{source_id}')
def archived_scientific_report(kind: ReportKind, source_id: str,
                                format: str = Query(default='json', pattern='^(json|md|html)$')):
    report = build_report(kind, source_id)
    if report is None:
        raise HTTPException(status_code=404, detail='Kaydedilmiş deney bulunamadı')
    if format == 'md':
        return Response(as_markdown(report), media_type='text/markdown; charset=utf-8',
                        headers={'Content-Disposition': f'attachment; filename="metaheuristic-{kind}-report.md"'})
    if format == 'html':
        return Response(as_html(report), media_type='text/html; charset=utf-8',
                        headers={'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
                                 'X-Content-Type-Options': 'nosniff'})
    return report


@app.post('/api/jobs/dimensional', status_code=status.HTTP_202_ACCEPTED)
def enqueue_dimensional(request: DimensionalRequest, http_request: Request):
    try:
        return http_request.app.state.job_queue.submit(request)
    except QueueFull as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.post('/api/jobs/benchmark', status_code=status.HTTP_202_ACCEPTED)
def enqueue_benchmark(request: BenchmarkSuiteRequest, http_request: Request):
    try:
        return http_request.app.state.job_queue.submit(request, kind='benchmark')
    except QueueFull as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.post('/api/jobs/sensitivity', status_code=status.HTTP_202_ACCEPTED)
def enqueue_sensitivity(request: SensitivityRequest, http_request: Request):
    try:
        return http_request.app.state.job_queue.submit(request, kind='sensitivity')
    except QueueFull as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.get('/api/jobs')
def list_jobs(http_request: Request):
    return {'jobs': http_request.app.state.job_queue.list()}


@app.get('/api/jobs/{job_id}')
def read_job(job_id: str, http_request: Request):
    try:
        return http_request.app.state.job_queue.read(job_id)
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail='Görev bulunamadı') from exc


@app.post('/api/jobs/{job_id}/cancel')
def cancel_job(job_id: str, http_request: Request):
    try:
        return http_request.app.state.job_queue.cancel(job_id)
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail='Görev bulunamadı') from exc


@app.get('/api/jobs/{job_id}/events')
def job_events(job_id: str, http_request: Request):
    try:
        return {'events': http_request.app.state.job_queue.events(job_id)}
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail='Görev bulunamadı') from exc


@app.post('/api/jobs/{job_id}/retry', status_code=status.HTTP_202_ACCEPTED)
def retry_job(job_id: str, http_request: Request):
    try:
        return http_request.app.state.job_queue.retry(job_id)
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail='Görev bulunamadı') from exc
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except QueueFull as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.delete('/api/jobs/{job_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_job_history(job_id: str, http_request: Request):
    try:
        http_request.app.state.job_queue.delete_history(job_id)
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail='Görev bulunamadı') from exc
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get('/api/jobs/{job_id}/result')
def job_result(job_id: str, http_request: Request):
    try:
        record = http_request.app.state.job_queue.read(job_id)
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail='Görev bulunamadı') from exc
    if record['state'] != 'completed':
        raise HTTPException(status_code=409, detail='Deney henüz tamamlanmadı')
    kind = record['kind']
    result = {'dimensional': load_dimensional,
              'benchmark': load_benchmark,
              'sensitivity': load_sensitivity}[kind](job_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Tamamlanan deney arşivde bulunamadı')
    return result
