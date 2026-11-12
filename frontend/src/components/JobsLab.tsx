import { useEffect, useState } from 'react';
import { Activity, Clock3, Database, Play, RefreshCcw, Square, CheckCircle2, XCircle, FileText, Trash2, History } from 'lucide-react';
import { cancelBackgroundJob, getBackgroundJobs, getBackgroundJobEvents, retryBackgroundJob, deleteBackgroundJob, getBackgroundResult, getSensitivityParameters, submitBackgroundJob } from '../lib/api';
import type { BackgroundJob, BackgroundJobEvent, BackgroundJobKind, DimensionalAlgorithm, DimensionalResult, BenchmarkResult, SensitivityResult, ParameterSpec } from '../lib/types';

const choices: DimensionalAlgorithm[] = ['pso','gwo','de','woa','mfo','ssa','fa','ba','gsa','abc','cs','sma','iwo','sa'];
const labels: Record<string,string> = {pso:'PSO',gwo:'GWO',de:'DE',woa:'WOA',mfo:'MFO',ssa:'SSA',fa:'FA',ba:'BA',gsa:'GSA',abc:'ABC',cs:'CS',sma:'SMA',iwo:'IWO',sa:'SA'};
const statuses: Record<string,string> = {queued:'Sırada bekliyor',running:'Hesaplanıyor',cancelling:'İptal istendi',completed:'Tamamlandı',cancelled:'İptal edildi',failed:'Hata oluştu'};
const kindNames: Record<BackgroundJobKind,string> = {dimensional:'Yüksek boyutlu',benchmark:'Çoklu benchmark',sensitivity:'Parametre duyarlılığı'};
const objectives2d=['sphere','rastrigin','ackley','rosenbrock','griewank','himmelblau','beale','booth'];
const clamp=(x:number,min:number,max:number)=>Math.max(min,Math.min(max,Number.isFinite(x)?Math.round(x):min));
const format=(n:number)=>n.toLocaleString('tr-TR');
const display=(n:number)=>Number.isFinite(n)?n.toPrecision(5):'—';

type ArchiveResult=DimensionalResult|BenchmarkResult|SensitivityResult;

export default function JobsLab(){
  const [kind,setKind]=useState<BackgroundJobKind>('dimensional');
  const [algorithms,setAlgorithms]=useState<DimensionalAlgorithm[]>(['pso','gwo','de']);
  const [objective,setObjective]=useState('rastrigin');
  const [benchmarkObjectives,setBenchmarkObjectives]=useState<string[]>(['sphere','rastrigin']);
  const [dimensions,setDimensions]=useState(10);
  const [population,setPopulation]=useState(24);
  const [iterations,setIterations]=useState(90);
  const [trials,setTrials]=useState(3);
  const [seed,setSeed]=useState(42);
  const [sensAlgorithm,setSensAlgorithm]=useState<DimensionalAlgorithm>('pso');
  const [specs,setSpecs]=useState<Record<string,ParameterSpec[]>>({});
  const [sensParameter,setSensParameter]=useState('pso_inertia_weight');
  const [sensValues,setSensValues]=useState('0.4, 0.72, 1');
  const [jobs,setJobs]=useState<BackgroundJob[]>([]);
  const [selected,setSelected]=useState<string|null>(null);
  const [result,setResult]=useState<ArchiveResult|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [events,setEvents]=useState<BackgroundJobEvent[]>([]);
  const [statusFilter,setStatusFilter]=useState('all');
  const active=jobs.find(j=>j.id===selected)??null;
  const visibleJobs=jobs.filter(j=>statusFilter==='all'||
    (statusFilter==='active'?['queued','running','cancelling'].includes(j.state):j.state===statusFilter));
  const parsedValues=sensValues.split(',').map(v=>Number(v.trim()));
  const validValues=parsedValues.length>=2&&parsedValues.length<=5&&parsedValues.every(Number.isFinite)&&new Set(parsedValues).size===parsedValues.length;
  const populationCap=kind==='sensitivity'?32:kind==='benchmark'?40:64;
  const iterationsCap=kind==='sensitivity'?120:kind==='benchmark'?150:200;
  const trialsCap=kind==='sensitivity'?5:kind==='dimensional'?20:8;
  const totalUnits=kind==='dimensional'?algorithms.length*trials:kind==='benchmark'?benchmarkObjectives.length*algorithms.length*trials:parsedValues.length*trials;
  const totalNfe=totalUnits*population*(iterations+1);
  const maximumNfe=kind==='benchmark'?200000:kind==='dimensional'?160000:Number.POSITIVE_INFINITY;
  const activeParameter=(specs[sensAlgorithm]??[]).find(s=>s.key===sensParameter);
  const valid=population<=populationCap&&iterations<=iterationsCap&&trials<=trialsCap&&
    (kind==='sensitivity' ? Boolean(activeParameter)&&validValues&&parsedValues.every(v=>v>=activeParameter!.minimum&&v<=activeParameter!.maximum&&(!activeParameter!.integral||Number.isInteger(v)))
      : algorithms.length>=2&&algorithms.length<=4&&(kind==='dimensional'||(benchmarkObjectives.length>=2&&benchmarkObjectives.length<=5)))&&totalNfe<=maximumNfe;
  const refresh=async()=>{try{setJobs(await getBackgroundJobs());}catch(e){setError(e instanceof Error?e.message:'Kuyruk erişilemiyor');}};
  useEffect(()=>{void refresh();const timer=window.setInterval(()=>{void refresh();},1500);return()=>window.clearInterval(timer);},[]);
  useEffect(()=>{getSensitivityParameters().then(setSpecs).catch(()=>{});},[]);
  useEffect(()=>{
    if(!selected){setEvents([]);return;}
    let stale=false;
    getBackgroundJobEvents(selected).then(items=>{if(!stale)setEvents(items);})
      .catch(()=>{if(!stale)setEvents([]);});
    return()=>{stale=true;};
  },[selected,active?.updated_at]);
  const toggleAlgorithm=(id:DimensionalAlgorithm)=>setAlgorithms(prev=>prev.includes(id)?
    (prev.length>2?prev.filter(x=>x!==id):prev):
    (prev.length<4?[...prev,id]:prev));
  const toggleObjective=(name:string)=>setBenchmarkObjectives(prev=>prev.includes(name)?
    (prev.length>2?prev.filter(o=>o!==name):prev):
    (prev.length<5?[...prev,name]:prev));
  const selectSensitivityAlgorithm=(id:DimensionalAlgorithm)=>{
    setSensAlgorithm(id);
    const first=specs[id]?.[0];
    if(first){setSensParameter(first.key);setSensValues(first.suggested.join(', '));}
  };
  const selectSensitivityParameter=(id:string)=>{
    setSensParameter(id);
    const param=specs[sensAlgorithm]?.find(x=>x.key===id);
    if(param)setSensValues(param.suggested.join(', '));
  };
  const create=async()=>{
    if(!valid)return;
    setBusy(true);setError(null);setResult(null);
    try{
      const common={population_size:population,iterations,trials,seed_start:seed,success_tolerance:.001};
      const config=kind==='dimensional'?{...common,algorithms,objective,dimensions}:
        kind==='benchmark'?{objectives:benchmarkObjectives,comparison:{...common,objective:'sphere',algorithms}}:
        {...common,algorithm:sensAlgorithm,objective,parameter:sensParameter,values:parsedValues};
      const job=await submitBackgroundJob(config,kind);
      setSelected(job.id);await refresh();
    }catch(e){setError(e instanceof Error?e.message:'Görev oluşturulamadı');}
    finally{setBusy(false);}
  };
  const cancel=async()=>{if(!selected)return;setBusy(true);setError(null);
    try{await cancelBackgroundJob(selected);await refresh();}
    catch(e){setError(e instanceof Error?e.message:'Görev iptal edilemedi');}
    finally{setBusy(false);}
  };
  const retry=async()=>{if(!selected)return;setBusy(true);setError(null);setResult(null);
    try{const next=await retryBackgroundJob(selected);setSelected(next.id);await refresh();}
    catch(e){setError(e instanceof Error?e.message:'Yeniden deneme oluşturulamadı');}
    finally{setBusy(false);}
  };
  const clearHistory=async()=>{if(!selected||!active)return;
    if(!window.confirm('Yalnızca görev geçmişi kaldırılsın mı? Tamamlanmış deneyin akademik arşivi korunur.'))return;
    setBusy(true);setError(null);
    try{await deleteBackgroundJob(selected);setSelected(null);setResult(null);setEvents([]);await refresh();}
    catch(e){setError(e instanceof Error?e.message:'Görev geçmişi kaldırılamadı');}
    finally{setBusy(false);}
  };
  const show=async(id:string)=>{setSelected(id);setResult(null);setError(null);
    try{setResult(await getBackgroundResult(id));}
    catch(e){setError(e instanceof Error?e.message:'Sonuç arşivden yüklenemedi');}
  };
  return <div className="jobs-lab">
    <section className="cmp-intro panel"><div className="cmp-intro-icon"><Clock3 size={23}/></div><div>
      <strong>Kalıcı deney görev kuyruğu</strong>
      <p>Yüksek boyut, benchmark matrisi veya parametre duyarlılığı deneylerini sıraya al. Her bağımsız koşudan sonra ilerlemeyi izle; tamamlanan işleri ilgili arşive kaydet.</p>
    </div><div className="cmp-budget"><span>AKTİF GÖREV</span><strong>{jobs.filter(j=>['queued','running','cancelling'].includes(j.state)).length}</strong></div></section>
    <div className="jobs-grid">
      <section className="panel jobs-config"><div className="panel-heading"><div><span className="label-overline">01 / DENEY TASARIMI</span><h2>Yeni görev oluştur</h2></div><Play size={18}/></div>
        <label className="bmk-field"><span>Deney türü</span><select aria-label="Deney türü" value={kind} onChange={e=>setKind(e.target.value as BackgroundJobKind)}>
          <option value="dimensional">Yüksek boyutlu optimizasyon</option><option value="benchmark">Çoklu benchmark (2D)</option><option value="sensitivity">Parametre duyarlılığı (OFAT, 2D)</option>
        </select></label>
        <p className="jobs-note">Algoritmaya özel gelişmiş katsayılar bu kuyruk formunda varsayılan değerlerindedir. Ayrıntılı özelleştirme için ilgili laboratuvarı kullan.</p>
        {kind!=='sensitivity'&&<><p className="jobs-mini-title">Algoritmalar (2–4)</p><div className="jobs-algorithms" aria-label="Arka plan algoritmaları">{choices.map(id=><label key={id} className="bmk-check"><input type="checkbox" checked={algorithms.includes(id)} disabled={(algorithms.length===2&&algorithms.includes(id))||(algorithms.length===4&&!algorithms.includes(id))} onChange={()=>toggleAlgorithm(id)}/><span>{labels[id]}</span></label>)}</div></>}
        {kind==='benchmark'&&<><p className="jobs-mini-title">Benchmark fonksiyonları (2–5)</p><div className="jobs-algorithms" aria-label="Benchmark fonksiyonları">{objectives2d.map(name=><label key={name} className="bmk-check"><input type="checkbox" checked={benchmarkObjectives.includes(name)} disabled={(benchmarkObjectives.length===2&&benchmarkObjectives.includes(name))||(benchmarkObjectives.length===5&&!benchmarkObjectives.includes(name))} onChange={()=>toggleObjective(name)}/><span>{name}</span></label>)}</div></>}
        {kind==='sensitivity'&&<>
          <label className="bmk-field"><span>Algoritma</span><select aria-label="Duyarlılık algoritması" value={sensAlgorithm} onChange={e=>selectSensitivityAlgorithm(e.target.value as DimensionalAlgorithm)}>{choices.map(id=><option key={id} value={id}>{labels[id]}</option>)}</select></label>
          <label className="bmk-field"><span>İncelenen parametre</span><select aria-label="İncelenen parametre" value={sensParameter} onChange={e=>selectSensitivityParameter(e.target.value)}>{(specs[sensAlgorithm]??[]).map(p=><option value={p.key} key={p.key}>{p.label} ({p.key})</option>)}</select></label>
          <label className="bmk-field"><span>Parametre değerleri (virgülle ayrılmış, 2–5 değer)</span><input aria-label="Parametre değerleri" value={sensValues} onChange={e=>setSensValues(e.target.value)} placeholder="0.4, 0.72, 1"/></label>
          {activeParameter&&<p className="jobs-note">Geçerli aralık: {activeParameter.minimum} – {activeParameter.maximum}{activeParameter.integral?' · Tam sayı':''}. Diğer parametreler sabit tutulur.</p>}
        </>}
        {kind!=='benchmark'&&<label className="bmk-field"><span>Amaç fonksiyonu</span><select value={objective} onChange={e=>setObjective(e.target.value)}>{(kind==='dimensional'?objectives2d.slice(0,5):objectives2d).map(o=><option value={o} key={o}>{o[0].toUpperCase()+o.slice(1)}</option>)}</select></label>}
        {kind==='dimensional'&&<label className="bmk-field"><span>Boyut sayısı</span><select value={dimensions} onChange={e=>setDimensions(Number(e.target.value))}>{[2,5,10,30].map(n=><option value={n} key={n}>{n} boyut</option>)}</select></label>}
        <div className="jobs-numbers">
          <label>Popülasyon <input type="number" value={population} min={8} max={populationCap} onChange={e=>setPopulation(clamp(Number(e.target.value),8,populationCap))}/></label>
          <label>İterasyon <input type="number" value={iterations} min={kind==='dimensional'?5:1} max={iterationsCap} onChange={e=>setIterations(clamp(Number(e.target.value),kind==='dimensional'?5:1,iterationsCap))}/></label>
          <label>Tekrar / tohum <input type="number" value={trials} min={2} max={trialsCap} onChange={e=>setTrials(clamp(Number(e.target.value),2,trialsCap))}/></label>
          <label>İlk tohum <input type="number" value={seed} min={0} max={2147483639} onChange={e=>setSeed(clamp(Number(e.target.value),0,2147483639))}/></label>
        </div>
        <div className="jobs-budget"><strong>Toplam değerlendirme bütçesi</strong><span>{format(totalNfe)} NFE · {totalUnits} koşu</span></div>
        {!valid&&<p role="alert" className="jobs-warning">Seçim veya NFE sınırı geçersiz. {kind==='sensitivity'?'2–5 farklı parametre değeri ve doğru parametre aralığı gerekli.':kind==='benchmark'?'2–5 fonksiyon ve en fazla 200.000 NFE gerekli.':'En fazla 160.000 NFE gerekli.'}</p>}
        <button className="button-primary" disabled={busy||!valid} onClick={()=>void create()}><Play size={16}/> Deneyi kuyruğa ekle</button>
      </section>
      <section className="panel jobs-queue"><div className="panel-heading"><div><span className="label-overline">02 / CANLI DURUM</span><h2>Görevler</h2></div><button className="button-subtle" onClick={()=>void refresh()} aria-label="Görevleri yenile"><RefreshCcw size={15}/> Yenile</button></div>
        <label className="jobs-filter"><span>Geçmiş filtresi</span><select aria-label="Görev durumu filtresi" value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}><option value="all">Bütün görevler</option><option value="active">Aktif görevler</option><option value="completed">Tamamlananlar</option><option value="failed">Hatalı olanlar</option><option value="cancelled">İptal edilenler</option></select></label>
        {error&&<div className="jobs-warning" role="alert">{error}</div>}
        {!jobs.length&&<p className="jobs-note">Henüz görev oluşturulmadı. Görevler SQLite'ta kalıcı saklanır.</p>}
        {jobs.length>0&&visibleJobs.length===0&&<p className="jobs-note">Bu filtreye uyan görev bulunmuyor.</p>}
        <div className="jobs-list">{visibleJobs.map(j=><button key={j.id} className={`jobs-item ${selected===j.id?'jobs-selected':''}`} onClick={()=>{setSelected(j.id);setResult(null);setError(null)}}>
          <span><strong>{kindNames[j.kind]} · {statuses[j.state]??j.state}</strong><small>{j.id.slice(0,8)} · {j.completed_units}/{j.total_units} koşu · {j.progress_percent.toFixed(1)}%</small></span><span className="jobs-status-icon">{j.state==='completed'?<CheckCircle2 size={19}/>:j.state==='failed'?<XCircle size={19}/>:<Clock3 size={19}/>}</span>
          <span className="jobs-progress"><i style={{width:`${j.progress_percent}%`}}/></span>
        </button>)}</div>
        {active&&<div className="jobs-detail"><h3>Seçilen görev</h3><p>Tür: <strong>{kindNames[active.kind]}</strong></p>
          <p>Durum: <strong>{statuses[active.state]??active.state}</strong></p>
          <p>İlerleme: {active.completed_units}/{active.total_units} bağımsız koşu</p>
          <p className="jobs-note">Diskte korunan checkpoint: {active.checkpoint_units} · Yeniden kullanılan koşu: {active.reused_units}</p>
          {active.active_algorithm&&<p>Son işlem: {active.active_algorithm}, tohum {active.active_seed}</p>}
          {active.state==='cancelling'&&<p className="jobs-note">Çalışan koşu tamamlandığında iptal uygulanacak.</p>}
          {active.restart_count>0&&<p className="jobs-restart" role="status">Bu görev sunucu kesintisinden sonra {active.restart_count} kez yeniden sıraya alındı. Doğrulanmış checkpoint'ler korunur; yalnızca eksik koşular hesaplanır.</p>}
          <p className="jobs-note">Çalıştırılma denemesi: {active.attempts}{active.retry_of?` · Önceki görev: ${active.retry_of.slice(0,8)}`:''}</p>
          {active.error&&<p role="alert" className="jobs-warning">{active.error}</p>}
          {['queued','running','cancelling'].includes(active.state)&&<button className="button-subtle" disabled={busy||active.state==='cancelling'} onClick={()=>void cancel()}><Square size={15}/> İptal iste</button>}
          {['failed','cancelled'].includes(active.state)&&<button className="button-subtle" disabled={busy} onClick={()=>void retry()}><RefreshCcw size={15}/> Görevi yeniden dene</button>}
          {active.state==='completed'&&<><button className="button-primary" onClick={()=>void show(active.id)}><Database size={16}/> Arşiv sonucunu aç</button><a className="report-action" href={`/api/reports/${active.kind}/${encodeURIComponent(active.id)}?format=html`} target="_blank" rel="noopener noreferrer"><FileText size={15}/> Akademik raporu aç</a></>}
          {['completed','failed','cancelled'].includes(active.state)&&<button className="button-subtle jobs-delete" disabled={busy} onClick={()=>void clearHistory()}><Trash2 size={15}/> Görev geçmişini kaldır</button>}
          <div className="jobs-events"><h4><History size={15}/> Görev olay geçmişi</h4>{!events.length?<p className="jobs-note">Henüz olay kaydı bulunmuyor.</p>:<ol aria-label="Görev olay geçmişi">{[...events].reverse().slice(0,24).map(ev=><li key={ev.id}><time dateTime={ev.created_at}>{new Date(ev.created_at).toLocaleString('tr-TR')}</time><span>{ev.message}</span></li>)}</ol>}</div>
        </div>}
        {result&&<div className="jobs-result"><h3>Arşivlenmiş deney</h3>
          <p>{'experiment_id' in result?`${result.parameters.objective.toUpperCase()} · ${result.parameters.dimensions} boyut`:'benchmark_id' in result?`${result.objectives.length} amaç fonksiyonu · ${result.algorithms.length} algoritma`:`${result.parameters.algorithm.toUpperCase()} · ${result.parameters.parameter}`}</p>
          <p>Toplam {format(result.total_evaluations)} NFE</p>
          <div className="jobs-summary">{'experiment_id' in result?result.groups.map(g=><div key={g.algorithm}><strong>{labels[g.algorithm]}</strong><span>Ort. hata: {display(g.mean_error)}</span><small>Başarı: {(g.success_rate*100).toFixed(1)}%</small></div>):'benchmark_id' in result?result.summary.map(g=><div key={g.algorithm}><strong>{labels[g.algorithm]}</strong><span>Ort. sıra: {display(g.mean_rank)}</span><small>Problem kazanımı: {g.objective_wins}</small></div>):result.groups.map(g=><div key={g.parameter_value}><strong>{result.parameters.parameter} = {g.parameter_value}</strong><span>Ort. hata: {display(g.mean_error)}</span><small>Başarı: {(g.success_rate*100).toFixed(1)}%</small></div>)}</div>
          <p className="jobs-note">Bu sonuç ilgili deney arşivinde ve Akademik Raporlar bölümünde de bulunur.</p>
        </div>}
      </section>
    </div>
    <section className="panel jobs-footer"><Activity size={20}/><p><strong>Yerel laboratuvar sınırları:</strong> Aynı anda bir çalışan görev ve en fazla sekiz aktif iş. İptal koşular arasında gerçekleşir. Sunucu kesintisinden sonra tamamlanmış koşular doğrulanmış checkpoint’lerden yüklenir; yalnızca eksik koşular yeniden hesaplanır. Tek bir algoritma koşusunun ortasından devam edilmez. Yeniden deneme yeni bir görev kimliği oluşturur. Geçmişten kaldırma akademik sonuç arşivini silmez. Kimlik doğrulama bulunmadığından uygulamayı internete açık dağıtmayın.</p></section>
  </div>;
}
