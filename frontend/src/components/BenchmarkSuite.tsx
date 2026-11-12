import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownToLine, BarChart3, CheckCircle2, Database, FlaskConical, Play, RotateCcw, Settings2 } from 'lucide-react';
import { getBenchmarkHistory, openBenchmark, runBenchmarkSuite } from '../lib/api';
import { COMPARISON_DEFAULT_CONFIG } from '../lib/comparisonDefaults';
import { downloadCsv, downloadJson, numberFmt } from '../lib/math';
import type { BenchmarkResult, BenchmarkRequest, Catalog, ComparisonAlgorithm, SavedBenchmark } from '../lib/types';

const ALGORITHMS: ComparisonAlgorithm[] = ['fa','pso','abc','mfo','gwo','woa','ba','ssa','sma','gsa','de','cs','iwo','sa'];
const NAME: Record<ComparisonAlgorithm,string>={
  fa:'Ateşböceği',pso:'Parçacık Sürüsü',abc:'Yapay Arı',mfo:'Güve-Alev',
  gwo:'Gri Kurt',woa:'Balina',ba:'Yarasa',ssa:'Salp Sürüsü',sma:'Cıvık Mantar',
  gsa:'Yerçekimsel Arama',de:'Diferansiyel Evrim',cs:'Guguk Kuşu',iwo:'İstilacı Ot',sa:'Tavlama',
};
const COLOR: Record<ComparisonAlgorithm,string>={
  fa:'#f5b46f',pso:'#6adbd0',abc:'#b6e890',mfo:'#e8a8da',
  gwo:'#95b9f5',woa:'#f4d27a',ba:'#e99b92',ssa:'#78d9af',
  sma:'#c3b1f5',gsa:'#68b7de',de:'#dfc883',cs:'#d9bbf2',iwo:'#9bc98e',sa:'#efb06c',
};
const defaults: BenchmarkRequest={
  objectives:['sphere','rastrigin','ackley','rosenbrock'],
  comparison:{...COMPARISON_DEFAULT_CONFIG,objective:'sphere',algorithms:['pso','gwo','de'],
    population_size:24,iterations:90,trials:3,seed_start:42,success_tolerance:0.001},
};
const fmt=(n:number,precision=5)=>numberFmt(n,precision);
function NumberField({title,value,min,max,onChange,step=1}:{title:string;value:number;min:number;max:number;step?:number;onChange:(value:number)=>void}){
  return <label className="bmk-field"><span>{title}</span><input type="number" min={min} max={max} step={step} value={value} onChange={e=>{
    const next=Number(e.target.value);if(e.target.value!==''&&Number.isFinite(next))onChange(Math.min(max,Math.max(min,next)));
  }}/></label>;
}

export default function BenchmarkSuite({catalog}:{catalog:Catalog|null}){
  const [config,setConfig]=useState<BenchmarkRequest>(defaults);
  const [result,setResult]=useState<BenchmarkResult|null>(null);
  const [history,setHistory]=useState<SavedBenchmark[]>([]);
  const [error,setError]=useState<string|null>(null);
  const [loading,setLoading]=useState(false);
  const [stale,setStale]=useState(false);
  const [openHistory,setOpenHistory]=useState(false);
  const [inspection,setInspection]=useState<string|null>(null);
  const budget=config.comparison.population_size*(config.comparison.iterations+1);
  const total=budget*config.comparison.trials*config.comparison.algorithms.length*config.objectives.length;
  const tooLarge=total>200_000;
  const options=useMemo(()=>catalog?.objectives??[],[catalog]);
  const update=(data:BenchmarkRequest)=>{setConfig(data);setStale(true)};
  const compareChange=<K extends keyof BenchmarkRequest['comparison']>(key:K,value:BenchmarkRequest['comparison'][K])=>{
    update({...config,comparison:{...config.comparison,[key]:value}});
  };
  const refresh=()=>getBenchmarkHistory().then(setHistory).catch(()=>{});
  useEffect(()=>{void refresh()},[]);
  function toggleObjective(name:string){
    const exists=config.objectives.includes(name);
    if(exists&&config.objectives.length<=2)return;
    if(!exists&&config.objectives.length>=5)return;
    update({...config,objectives:exists?config.objectives.filter(id=>id!==name):[...config.objectives,name]});
  }
  function toggleAlgorithm(id:ComparisonAlgorithm){
    const selected=config.comparison.algorithms;
    const exists=selected.includes(id);
    if(exists&&selected.length<=2)return;
    if(!exists&&selected.length>=4)return;
    const algorithms=ALGORITHMS.filter(a=>exists ? (selected.includes(a)&&a!==id) : (selected.includes(a)||a===id));
    // Preserve original catalog order regardless of the click order.
    compareChange('algorithms',algorithms);
  }
  async function start(){
    setLoading(true);setError(null);
    try{
      const res=await runBenchmarkSuite(config);
      setResult(res);setInspection(res.objectives[0]);setStale(false);
      void refresh();
    }catch(e){setError(e instanceof Error?e.message:'Benchmark başarısız');}
    finally{setLoading(false);}
  }
  async function restore(id:string){
    setLoading(true);setError(null);
    try{
      const res=await openBenchmark(id);
      setResult(res);setInspection(res.objectives[0]);setStale(false);
      setConfig({...res.parameters,comparison:{...COMPARISON_DEFAULT_CONFIG,...res.parameters.comparison}});
      setOpenHistory(false);
    }catch(e){setError(e instanceof Error?e.message:'Arşiv açılamadı');}
    finally{setLoading(false);}
  }
  const csvExport=()=>{
    if(!result)return;
    const rows=result.rows.flatMap(r=>r.cells.flatMap(c=>c.trials.map(t=>({
      objective:r.objective,algorithm:c.algorithm,seed:t.seed,
      best_value:t.best_value,absolute_error:t.absolute_error,
      rank:c.rank,success:t.absolute_error<=result.success_tolerance?1:0,
      nfe:t.function_evaluations,first_success_nfe:t.first_success_evaluations??'',
      duration_ms:t.duration_ms,
    }))));
    downloadCsv(rows,`benchmark-${result.benchmark_id.slice(0,8)}.csv`);
  };
  const selectedRow=result?.rows.find(row=>row.objective===inspection)??result?.rows[0];
  return <div className="bmk-lab">
    <div className="cmp-intro panel"><div className="cmp-intro-icon"><FlaskConical size={24}/></div>
      <div><strong>Çoklu benchmark · 8 test fonksiyonu</strong><p>Birden fazla probleme aynı algoritmaları ve aynı tohumları uygula; hata, başarı oranı ve problem içi sıralamaları karşılaştır. Önceki simülasyonlar korunur.</p></div>
      <div className="cmp-budget"><span>HESAPLAMA BÜTÇESİ</span><strong>{budget.toLocaleString('tr-TR')} NFE / koşu</strong></div>
    </div>
    <div className="bmk-layout">
      <section className="panel bmk-controls"><div className="panel-heading"><div><span className="label-overline">01 / DENEY TASARIMI</span><h2>Benchmark ayarları</h2></div><Settings2 size={18}/></div>
        <div className="bmk-control-inner">
          <div className="bmk-select-group"><strong>TEST FONKSİYONLARI · 2–5 ({config.objectives.length}/5)</strong>
            <div className="bmk-check-grid">{options.map(o=><label key={o.id} className="bmk-check"><input type="checkbox" checked={config.objectives.includes(o.id)} disabled={config.objectives.includes(o.id)?config.objectives.length<=2:config.objectives.length>=5} onChange={()=>toggleObjective(o.id)}/><span>{o.name}<small>{o.description}</small></span></label>)}</div>
          </div>
          <div className="bmk-select-group"><strong>ALGORİTMALAR · 2–4 ({config.comparison.algorithms.length}/4)</strong>
            <div className="bmk-check-grid">{ALGORITHMS.map(id=><label key={id} className="bmk-check"><input type="checkbox" checked={config.comparison.algorithms.includes(id)} disabled={config.comparison.algorithms.includes(id)?config.comparison.algorithms.length<=2:config.comparison.algorithms.length>=4} onChange={()=>toggleAlgorithm(id)}/><span><i className="bmk-color" style={{background:COLOR[id]}}/>{NAME[id]} <small>{id.toUpperCase()}</small></span></label>)}</div>
          </div>
          <div className="bmk-numeric-grid">
            <NumberField title="Ajan sayısı" value={config.comparison.population_size} min={5} max={40} onChange={v=>compareChange('population_size',Math.trunc(v))}/>
            <NumberField title="Referans adım" value={config.comparison.iterations} min={1} max={150} onChange={v=>compareChange('iterations',Math.trunc(v))}/>
            <NumberField title="Tekrar sayısı" value={config.comparison.trials} min={2} max={8} onChange={v=>compareChange('trials',Math.trunc(v))}/>
            <NumberField title="İlk rastgele tohum" value={config.comparison.seed_start} min={0} max={2147483639} onChange={v=>compareChange('seed_start',Math.trunc(v))}/>
            <NumberField title="Başarı eşiği" value={config.comparison.success_tolerance} min={.00000001} max={100} step={.0001} onChange={v=>compareChange('success_tolerance',v)}/>
          </div>
          <div className="bmk-budget-note"><strong>{total.toLocaleString('tr-TR')} gerçek fonksiyon değerlendirmesi</strong><span>{config.objectives.length} fonksiyon × {config.comparison.algorithms.length} algoritma × {config.comparison.trials} tohum</span><span>Varsayılan algoritma parametreleri kullanılır. Ayrıntılı parametre ayarı Karşılaştırma Laboratuvarı'ndadır.</span></div>
          {tooLarge&&<div className="cmp-warning">200.000 NFE üst sınırı aşıldı. Deney boyutunu küçült.</div>}
          {stale&&result&&<div className="cmp-warning">Ayarlar değişti. Görüntülenen sonuç önceki deneye aittir.</div>}
          <button className="button-primary bmk-run" disabled={!catalog||loading||tooLarge} onClick={start}>{loading?<span className="spinner"/>:<Play size={16} fill="currentColor"/>}{loading?'Benchmark çalıştırılıyor…':'Benchmarkı başlat'}</button>
        </div>
      </section>
      <div className="bmk-main">
        {error&&<div className="cmp-alert" role="alert">{error}<button aria-label="Hatayı kapat" onClick={()=>setError(null)}>×</button></div>}
        {result? <>
          <section className="bmk-top-grid">
            <div className="bmk-kpi"><span>FONKSİYON</span><strong>{result.objectives.length}</strong><small>Bağımsız problem</small></div>
            <div className="bmk-kpi"><span>ALGORİTMA</span><strong>{result.algorithms.length}</strong><small>Sürekli optimizasyon</small></div>
            <div className="bmk-kpi"><span>TOPLAM NFE</span><strong>{result.total_evaluations.toLocaleString('tr-TR')}</strong><small>Tüm koşular</small></div>
            <div className="bmk-kpi"><span>İLK ORT. SIRA</span><strong>{fmt(result.summary[0].mean_rank,2)}</strong><small>{result.summary[0].algorithm.toUpperCase()} · yalnızca seçilen problemler</small></div>
          </section>
          <section className="panel bmk-matrix-panel"><div className="panel-heading"><div><span className="label-overline">02 / ÇOKLU PROBLEM MATRİSİ</span><h2>Optimumdan ortalama mutlak hata</h2></div><div className="cmp-export"><button onClick={csvExport}><ArrowDownToLine size={15}/> CSV</button><button onClick={()=>downloadJson(result,`benchmark-${result.benchmark_id.slice(0,8)}.json`)}><ArrowDownToLine size={15}/> JSON</button></div></div>
            <p className="bmk-section-note">Her hücre aynı problemin kendi optimumuna göre hesaplanır. Yeşil, o fonksiyonda en düşük ortalama hatayı; sıra numarası eşitlikleri hesaba katarak konumu gösterir.</p>
            <div className="cmp-table-scroll"><table className="cmp-table bmk-matrix"><thead><tr><th>Fonksiyon</th>{result.algorithms.map(id=><th key={id}><span className="bmk-color" style={{background:COLOR[id]}}/>{id.toUpperCase()}</th>)}</tr></thead><tbody>{result.rows.map(row=><tr key={row.objective}>
              <td><button className="bmk-row-link" onClick={()=>setInspection(row.objective)}>{options.find(o=>o.id===row.objective)?.name??row.objective}</button><small>f* = {fmt(row.optimum_value)}</small></td>
              {row.cells.map(cell=><td key={cell.algorithm} className={cell.rank===1?'bmk-best-cell':''}><div className="bmk-cell"><strong>{fmt(cell.mean_error,5)}</strong><small>Sıra {fmt(cell.rank,1)} · Başarı %{(cell.success_rate*100).toFixed(0)}</small></div></td>)}
            </tr>)}</tbody></table></div>
          </section>
          <section className="panel bmk-summary-panel"><div className="panel-heading"><div><span className="label-overline">03 / ÇOKLU PROBLEM ÖZETİ</span><h2>Ortalama sıralama ve başarı</h2></div><BarChart3 size={18}/></div>
            <p className="bmk-section-note">Ortalama sıra küçükse daha iyi; bu yalnızca seçili problem kümesine ait betimsel bir ölçüttür ve istatistiksel üstünlük kanıtı değildir.</p>
            <div className="bmk-rank-list">{result.summary.map(s=><div className="bmk-rank-row" key={s.algorithm}>
              <div className="bmk-rank-name"><i className="bmk-color" style={{background:COLOR[s.algorithm]}}/><strong>{NAME[s.algorithm]}</strong><small>{s.algorithm.toUpperCase()}</small></div>
              <div className="bmk-rank-track"><div style={{width:`${Math.max(5,100*(result.algorithms.length+1-s.mean_rank)/result.algorithms.length)}%`,background:COLOR[s.algorithm]}}/></div>
              <div className="bmk-rank-values"><b>{fmt(s.mean_rank,2)} sıra</b><small>%{(s.mean_success_rate*100).toFixed(0)} başarı · {s.objective_wins} birincilik</small></div>
            </div>)}</div>
          </section>
          {selectedRow&&<section className="panel bmk-detail-panel"><div className="panel-heading"><div><span className="label-overline">04 / PROBLEM İNCELEMESİ</span><h2>Tohum bazında sonuçlar</h2></div><select aria-label="İncelenecek fonksiyon" value={selectedRow.objective} onChange={e=>setInspection(e.target.value)}>{result.rows.map(row=><option value={row.objective} key={row.objective}>{options.find(o=>o.id===row.objective)?.name??row.objective}</option>)}</select></div>
            <div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>Tohum</th>{selectedRow.cells.map(c=><th key={c.algorithm}>{c.algorithm.toUpperCase()} · Hata</th>)}<th>NFE</th></tr></thead><tbody>{result.seeds.map((seed,i)=><tr key={seed}><td>{seed}</td>{selectedRow.cells.map(c=><td key={c.algorithm}>{fmt(c.trials[i].absolute_error,6)}</td>)}<td>{result.evaluations_per_run.toLocaleString('tr-TR')}</td></tr>)}</tbody></table></div>
          </section>}
          <div className="cmp-method"><CheckCircle2 size={17}/><div><strong>Bilimsel yöntem</strong><p>{result.methodology} Kayıt: {result.benchmark_id.slice(0,8)}.</p></div></div>
        </>:<div className="panel bmk-empty"><Activity size={30}/><h2>Çoklu benchmark deneyini başlat</h2><p>En az iki amaç fonksiyonu ve iki algoritma seç. Sonuçlar tek tek koşularda hesaplanır, SQLite'a kaydedilir; başarı oranları ve ortalama sıralamalarla analiz edilir.</p></div>}
        <section className="panel cmp-history"><div className="panel-heading"><div><span className="label-overline">05 / KALICI BENCHMARK ARŞİVİ</span><h2>Önceki test kümeleri</h2></div><button className="cmp-history-toggle" onClick={()=>setOpenHistory(v=>!v)}><Database size={15}/>{openHistory?'Gizle':`Arşivi aç (${history.length})`}</button></div>
          {openHistory&&<div className="cmp-history-body">{history.length?history.map(h=><div className="cmp-history-row" key={h.benchmark_id}><div><strong>{h.objectives.map(o=>o.toUpperCase()).join(' · ')}</strong><small>{h.algorithms.join(' + ').toUpperCase()} · {h.trials_per_algorithm} koşu / algoritma · {new Date(h.created_at).toLocaleString('tr-TR')}</small></div><button className="button-subtle" disabled={loading} onClick={()=>restore(h.benchmark_id)}><RotateCcw size={14}/> Yeniden aç</button></div>):<p>Henüz kaydedilmiş benchmark yok.</p>}</div>}
        </section>
      </div>
    </div>
  </div>;
}
