import type { Catalog, Config, Run } from './types';

export async function getCatalog(): Promise<Catalog> {
  const response = await fetch('/api/catalog');
  if (!response.ok) throw new Error('Algoritma kataloğu yüklenemedi. Backend çalışıyor mu?');
  return response.json() as Promise<Catalog>;
}

export async function runSimulation(config: Config, signal?: AbortSignal): Promise<Run> {
  const response = await fetch('/api/simulations', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config), signal,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(response.status === 422 ? `Parametreler geçersiz: ${JSON.stringify(detail?.detail ?? '')}` : 'Simülasyon oluşturulamadı.');
  }
  return response.json() as Promise<Run>;
}

export async function runComparison(config: import('./types').ComparisonConfig): Promise<import('./types').ComparisonResult> {
  const response = await fetch('/api/comparisons', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(response.status === 422
      ? `Karşılaştırma parametreleri geçersiz: ${JSON.stringify(detail?.detail ?? '')}`
      : 'Karşılaştırma çalıştırılamadı. Backend bağlantısını kontrol et.');
  }
  return response.json() as Promise<import('./types').ComparisonResult>;
}

export async function getComparisonHistory(): Promise<import('./types').SavedComparison[]> {
  const response = await fetch('/api/comparisons');
  if (!response.ok) throw new Error('Kayıtlı karşılaştırmalar yüklenemedi.');
  const body = await response.json() as {comparisons: import('./types').SavedComparison[]};
  return body.comparisons;
}

export async function openComparison(id: string): Promise<import('./types').ComparisonResult> {
  const response = await fetch(`/api/comparisons/${encodeURIComponent(id)}`);
  if (!response.ok) throw new Error('Karşılaştırma kaydı açılamadı.');
  return response.json() as Promise<import('./types').ComparisonResult>;
}

export async function runAcoSimulation(config: import('./types').AcoConfig, signal?: AbortSignal): Promise<import('./types').AcoRun> {
  const response = await fetch('/api/aco/simulations', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(config), signal,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(response.status === 422
      ? `ACO parametreleri geçersiz: ${JSON.stringify(detail?.detail ?? '')}`
      : 'Karınca Kolonisi hesaplanamadı. Backend bağlantısını kontrol et.');
  }
  return response.json() as Promise<import('./types').AcoRun>;
}


export async function runBenchmarkSuite(config: import('./types').BenchmarkRequest): Promise<import('./types').BenchmarkResult> {
  const response = await fetch('/api/benchmarks', {
    method: 'POST', headers: {'Content-Type':'application/json'}, body:JSON.stringify(config),
  });
  if (!response.ok) {
    const detail = await response.json().catch(()=>null);
    throw new Error(response.status===422
      ? `Benchmark ayarları geçersiz: ${JSON.stringify(detail?.detail??'')}`
      : 'Benchmark oluşturulamadı. Backend bağlantısını kontrol et.');
  }
  return response.json() as Promise<import('./types').BenchmarkResult>;
}

export async function getBenchmarkHistory(): Promise<import('./types').SavedBenchmark[]> {
  const response = await fetch('/api/benchmarks');
  if(!response.ok)throw new Error('Benchmark arşivi açılamadı');
  const data=await response.json() as {benchmarks:import('./types').SavedBenchmark[]};
  return data.benchmarks;
}

export async function openBenchmark(id:string): Promise<import('./types').BenchmarkResult> {
  const response=await fetch(`/api/benchmarks/${encodeURIComponent(id)}`);
  if(!response.ok)throw new Error('Benchmark kaydı bulunamadı');
  return response.json() as Promise<import('./types').BenchmarkResult>;
}

export async function getSensitivityParameters():Promise<Record<string,import('./types').ParameterSpec[]>>{
  const response=await fetch('/api/sensitivity/parameters');
  if(!response.ok)throw new Error('Parametre kataloğu yüklenemedi. Backend çalışıyor mu?');
  const data=await response.json() as {parameters:Record<string,import('./types').ParameterSpec[]>};
  return data.parameters;
}
export async function runSensitivity(config:import('./types').SensitivityConfig):Promise<import('./types').SensitivityResult>{
  const response=await fetch('/api/sensitivity',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
  if(!response.ok){const data=await response.json().catch(()=>null);throw new Error(response.status===422
    ? `Parametreler geçersiz: ${JSON.stringify(data?.detail??'')}`:'Duyarlılık deneyi çalıştırılamadı. Backend bağlantısını kontrol et.');}
  return response.json() as Promise<import('./types').SensitivityResult>;
}
export async function getSensitivityHistory():Promise<import('./types').SavedSensitivity[]>{
  const response=await fetch('/api/sensitivity');
  if(!response.ok)throw new Error('Duyarlılık arşivi yüklenemedi.');
  const data=await response.json() as {studies:import('./types').SavedSensitivity[]};
  return data.studies;
}
export async function openSensitivity(id:string):Promise<import('./types').SensitivityResult>{
  const response=await fetch(`/api/sensitivity/${encodeURIComponent(id)}`);
  if(!response.ok)throw new Error('Duyarlılık kaydı açılamadı.');
  return response.json() as Promise<import('./types').SensitivityResult>;
}

export async function runDimensional(config:import('./types').DimensionalConfig):Promise<import('./types').DimensionalResult>{
  const response=await fetch('/api/dimensional',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
  if(!response.ok){const data=await response.json().catch(()=>null);throw new Error(response.status===422
    ? `Yüksek boyut ayarları geçersiz: ${JSON.stringify(data?.detail??'')}`:'Yüksek boyutlu deney çalıştırılamadı. Backend bağlantısını kontrol et.');}
  return response.json() as Promise<import('./types').DimensionalResult>;
}
export async function getDimensionalHistory():Promise<import('./types').SavedDimensional[]>{
  const response=await fetch('/api/dimensional');
  if(!response.ok)throw new Error('Yüksek boyutlu deney arşivi açılamadı.');
  const data=await response.json() as {experiments:import('./types').SavedDimensional[]};
  return data.experiments;
}
export async function openDimensional(id:string):Promise<import('./types').DimensionalResult>{
  const response=await fetch(`/api/dimensional/${encodeURIComponent(id)}`);
  if(!response.ok)throw new Error('Yüksek boyutlu deney kaydı bulunamadı.');
  return response.json() as Promise<import('./types').DimensionalResult>;
}

export function reportUrl(kind:import('./types').ReportKind,id:string,format:'json'|'html'|'md'='json'):string {
  return `/api/reports/${encodeURIComponent(kind)}/${encodeURIComponent(id)}?format=${format}`;
}
export async function getReportHistory():Promise<import('./types').ReportEntry[]> {
  const response=await fetch('/api/reports');
  if(!response.ok)throw new Error('Akademik rapor arşivine ulaşılamadı. Backend çalışıyor mu?');
  const data=await response.json() as {reports:import('./types').ReportEntry[]};
  return data.reports;
}
export async function getReport(kind:import('./types').ReportKind,id:string):Promise<import('./types').ScientificReport>{
  const response=await fetch(reportUrl(kind,id));
  if(!response.ok)throw new Error('Kaydedilmiş deney raporu bulunamadı.');
  return response.json() as Promise<import('./types').ScientificReport>;
}

export async function submitBackgroundJob(config:object,kind:import('./types').BackgroundJobKind='dimensional'):Promise<import('./types').BackgroundJob>{
  const r=await fetch(`/api/jobs/${kind}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
  if(!r.ok){const body=await r.json().catch(()=>null);throw new Error(`Görev kabul edilmedi (${r.status}): ${JSON.stringify(body?.detail??'')}`);}
  return r.json() as Promise<import('./types').BackgroundJob>;
}
export async function getBackgroundJobs():Promise<import('./types').BackgroundJob[]>{
  const r=await fetch('/api/jobs');if(!r.ok)throw new Error('Görev kuyruğuna ulaşılamıyor');
  const body=await r.json() as {jobs:import('./types').BackgroundJob[]};return body.jobs;
}
export async function cancelBackgroundJob(id:string):Promise<import('./types').BackgroundJob>{
  const r=await fetch(`/api/jobs/${encodeURIComponent(id)}/cancel`,{method:'POST'});
  if(!r.ok)throw new Error('Görev iptali gönderilemedi');
  return r.json() as Promise<import('./types').BackgroundJob>;
}
export async function getBackgroundResult(id:string):Promise<import('./types').DimensionalResult|import('./types').BenchmarkResult|import('./types').SensitivityResult>{
  const r=await fetch(`/api/jobs/${encodeURIComponent(id)}/result`);
  if(!r.ok)throw new Error('Görev sonucu bulunamadı veya henüz hazır değil');
  return r.json() as Promise<import('./types').DimensionalResult|import('./types').BenchmarkResult|import('./types').SensitivityResult>;
}

export async function getBackgroundJobEvents(id:string):Promise<import('./types').BackgroundJobEvent[]>{
  const r=await fetch(`/api/jobs/${encodeURIComponent(id)}/events`);
  if(!r.ok)throw new Error('Görev olay geçmişi yüklenemedi');
  const body=await r.json() as {events:import('./types').BackgroundJobEvent[]};
  return body.events;
}
export async function retryBackgroundJob(id:string):Promise<import('./types').BackgroundJob>{
  const r=await fetch(`/api/jobs/${encodeURIComponent(id)}/retry`,{method:'POST'});
  if(!r.ok){const body=await r.json().catch(()=>null);throw new Error(`Tekrar oluşturulamadı (${r.status}): ${body?.detail??''}`);}
  return r.json() as Promise<import('./types').BackgroundJob>;
}
export async function deleteBackgroundJob(id:string):Promise<void>{
  const r=await fetch(`/api/jobs/${encodeURIComponent(id)}`,{method:'DELETE'});
  if(!r.ok){const body=await r.json().catch(()=>null);throw new Error(`Geçmiş kaydı kaldırılamadı (${r.status}): ${body?.detail??''}`);}
}

export async function getScienceAudit(id:string):Promise<import('./types').ScienceAudit>{
  const r=await fetch(`/api/science/dimensional/${encodeURIComponent(id)}`);
  if(!r.ok)throw new Error(r.status===404?'Deney arşivde bulunamadı.':'Bilimsel denetim yüklenemedi.');
  return r.json() as Promise<import('./types').ScienceAudit>;
}
