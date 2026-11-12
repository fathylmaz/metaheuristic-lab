import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownToLine, Database, FlaskConical, Play, Settings2, SlidersHorizontal } from 'lucide-react';
import { getSensitivityHistory,getSensitivityParameters,openSensitivity,runSensitivity } from '../lib/api';
import { downloadCsv,downloadJson,numberFmt } from '../lib/math';
import type { Catalog, ComparisonAlgorithm, ParameterSpec, SavedSensitivity, SensitivityConfig, SensitivityResult } from '../lib/types';

const LABELS: Record<ComparisonAlgorithm,string>={fa:'Ateşböceği (FA)',pso:'Parçacık Sürüsü (PSO)',abc:'Yapay Arı (ABC)',
  cs:'Guguk Kuşu (CS)',mfo:'Güve-Alev (MFO)',gwo:'Gri Kurt (GWO)',woa:'Balina (WOA)',ba:'Yarasa (BA)',
  ssa:'Salp Sürüsü (SSA)',sma:'Cıvık Mantar (SMA)',iwo:'İstilacı Yabani Ot (IWO)',sa:'Tavlama (SA)',
  gsa:'Yerçekimsel Arama (GSA)',de:'Diferansiyel Evrim (DE)'};
const COLORS=['#6de1c4','#f6b76e','#a9bbfa','#dfaae9','#e7cd7d'];
const initial:SensitivityConfig={algorithm:'pso',objective:'rastrigin',parameter:'pso_inertia_weight',values:[.4,.72,1],
  population_size:24,iterations:60,trials:3,seed_start:42,success_tolerance:.001};
const fmt=(v:number,n=5)=>numberFmt(v,n);
function Numeric({label,value,min,max,step=1,onChange}:{label:string;value:number;min:number;max:number;step?:number;onChange:(v:number)=>void}){
  return <label className="bmk-field"><span>{label}</span><input type="number" min={min} max={max} step={step} value={value} onChange={e=>{
    if(e.target.value==='')return;const n=Number(e.target.value);if(Number.isFinite(n))onChange(Math.min(max,Math.max(min,n)));
  }}/></label>;
}
function Curves({result}:{result:SensitivityResult}){
  const width=720,height=250,left=54,right=16,top=16,bottom=34;
  const points=result.groups[0]?.curve??[];
  if(points.length<2)return null;
  const values=result.groups.flatMap(g=>g.curve.map(p=>Math.log10(Math.max(p.mean_error,1e-16))));
  const vmin=Math.min(-1,...values),vmax=Math.max(0,...values);
  const x=(n:number)=>left+(n-result.evaluations_per_run/points.length)/Math.max(1,result.evaluations_per_run-result.evaluations_per_run/points.length)*(width-left-right);
  const y=(n:number)=>top+(vmax-Math.log10(Math.max(n,1e-16)))/Math.max(1e-9,vmax-vmin)*(height-top-bottom);
  return <div className="sens-chart-wrap"><div className="sens-legend">{result.groups.map((g,i)=><span key={g.parameter_value}>
    <i style={{backgroundColor:COLORS[i]}}/> {result.parameters.parameter} = {g.parameter_value}</span>)}</div>
    <svg role="img" aria-label="NFE başına ortalama mutlak hata, logaritmik ölçek" viewBox={`0 0 ${width} ${height}`} className="sens-chart">
      {[0,.25,.5,.75,1].map(frac=><g key={frac}><line x1={left} x2={width-right} y1={top+frac*(height-top-bottom)} y2={top+frac*(height-top-bottom)} stroke="#466070" strokeDasharray="4 7" opacity=".55"/>
        <text x={left-9} y={top+frac*(height-top-bottom)+4} textAnchor="end" fill="#91b5bf" fontSize="11">10^{Math.round(vmax-frac*(vmax-vmin))}</text></g>)}
      {result.groups.map((g,i)=><path key={i} d={g.curve.map((p,j)=>`${j===0?'M':'L'}${x(p.evaluations).toFixed(1)} ${y(p.mean_error).toFixed(1)}`).join(' ')}
        fill="none" stroke={COLORS[i]} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round"/>)}
      {[0,.25,.5,.75,1].map(k=><text key={k} x={left+k*(width-left-right)} y={height-13} fill="#91b5bf" fontSize="11" textAnchor="middle">{Math.round((result.evaluations_per_run/points.length)+k*(result.evaluations_per_run-result.evaluations_per_run/points.length))}</text>)}
      <text x={width/2} y={height-1} textAnchor="middle" fill="#93bdc2" fontSize="11">Fonksiyon değerlendirmesi (NFE)</text>
    </svg><p>Y ekseni log₁₀: sıfır hatalar yalnızca çizimde 10⁻¹⁶ tabanıyla gösterilir. Çizgiler her tohumdaki en iyi hata değerlerinin ortalamasıdır.</p>
  </div>;
}
export default function SensitivityLab({catalog}:{catalog:Catalog|null}){
  const [specs,setSpecs]=useState<Record<string,ParameterSpec[]>>({});
  const [config,setConfig]=useState<SensitivityConfig>(initial);
  const [valueText,setValueText]=useState('0.4, 0.72, 1.0');
  const [result,setResult]=useState<SensitivityResult|null>(null);
  const [history,setHistory]=useState<SavedSensitivity[]>([]);
  const [showHistory,setShowHistory]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [loading,setLoading]=useState(false);
  const [stale,setStale]=useState(false);
  const items=specs[config.algorithm]??[];
  const spec=items.find(p=>p.key===config.parameter)??items[0];
  const parsed=useMemo(()=>valueText.split(/[;,\s]+/).filter(Boolean).map(s=>Number(s)),[valueText]);
  const valid=!!spec&&parsed.length>=2&&parsed.length<=5&&new Set(parsed).size===parsed.length&&
    parsed.every(v=>Number.isFinite(v)&&v>=spec.minimum&&v<=spec.maximum&&(!spec.integral||Number.isInteger(v)));
  const budget=config.population_size*(config.iterations+1);
  const total=budget*config.trials*parsed.length;
  const tooLarge=total>105000;
  const update=(changes:Partial<SensitivityConfig>)=>{setConfig(prev=>({...prev,...changes}));setStale(true)};
  const refresh=()=>getSensitivityHistory().then(setHistory).catch(()=>{});
  useEffect(()=>{getSensitivityParameters().then(setSpecs).catch(e=>setError(String(e)));void refresh();},[]);
  function selectAlgorithm(algorithm:ComparisonAlgorithm){
    const first=specs[algorithm]?.[0];if(!first)return;
    update({algorithm,parameter:first.key,values:first.suggested});setValueText(first.suggested.join(', '));
  }
  function selectParameter(parameter:string){
    const next=items.find(p=>p.key===parameter);if(!next)return;
    update({parameter,values:next.suggested});setValueText(next.suggested.join(', '));
  }
  async function start(){
    if(!valid||tooLarge)return;
    setLoading(true);setError(null);
    try{const data=await runSensitivity({...config,values:parsed});setResult(data);setStale(false);void refresh();}
    catch(e){setError(e instanceof Error?e.message:'Duyarlılık çalıştırılamadı');}
    finally{setLoading(false);}
  }
  async function open(id:string){
    setLoading(true);setError(null);
    try{const data=await openSensitivity(id);setResult(data);setConfig(data.parameters);setValueText(data.parameters.values.join(', '));setStale(false);setShowHistory(false);}
    catch(e){setError(e instanceof Error?e.message:'Arşiv açılamadı');}
    finally{setLoading(false);}
  }
  const exportCsv=()=>{
    if(!result)return;
    downloadCsv(result.groups.flatMap(g=>g.trials.map(t=>({algorithm:result.parameters.algorithm,objective:result.parameters.objective,
      parameter:result.parameters.parameter,parameter_value:g.parameter_value,seed:t.seed,best_value:t.best_value,
      absolute_error:t.absolute_error,mean_error:g.mean_error,std_error:g.std_error,
      success:t.first_success_nfe===null?0:1,first_success_nfe:t.first_success_nfe??'',
      function_evaluations:t.function_evaluations,duration_ms:t.duration_ms}))),`sensitivity-${result.sensitivity_id.slice(0,8)}.csv`);
  };
  const winner=result ? result.groups.reduce((best,g)=>g.mean_error<best.mean_error?g:best,result.groups[0]) : undefined;
  return <div className="sens-lab">
    <div className="cmp-intro panel"><div className="cmp-intro-icon"><SlidersHorizontal size={22}/></div>
      <div><strong>Parametre Duyarlılığı · Tek değişkenli (OFAT) deney</strong><p>Algoritmanın tek bir parametresini değiştir; diğer ayarları, tohumları ve gerçek NFE bütçesini sabit tutarak etkisini ölç.</p></div>
      <div className="cmp-budget"><span>EŞİT HESAPLAMA BÜTÇESİ</span><strong>{budget.toLocaleString('tr-TR')} NFE / koşu</strong></div>
    </div>
    <div className="sens-layout">
      <section className="panel sens-controls"><div className="panel-heading"><div><span className="label-overline">01 / DENEY TASARIMI</span><h2>Parametre ayarları</h2></div><Settings2 size={18}/></div>
        <div className="sens-fields">
          <label className="bmk-field"><span>Algoritma</span><select value={config.algorithm} onChange={e=>selectAlgorithm(e.target.value as ComparisonAlgorithm)}>
            {(Object.keys(LABELS) as ComparisonAlgorithm[]).map(id=><option value={id} key={id}>{LABELS[id]}</option>)}</select></label>
          <label className="bmk-field"><span>Amaç fonksiyonu</span><select value={config.objective} onChange={e=>update({objective:e.target.value})}>
            {(catalog?.objectives??[]).map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select></label>
          <label className="bmk-field"><span>İncelenecek parametre</span><select value={config.parameter} onChange={e=>selectParameter(e.target.value)}>
            {items.map(p=><option key={p.key} value={p.key}>{p.label}</option>)}</select></label>
          <label className="bmk-field"><span>Parametre değerleri (2–5)</span><input type="text" value={valueText} onChange={e=>{setValueText(e.target.value);setStale(true)}} placeholder="0.4, 0.72, 1.0"/>
            {spec&&<small>İzin verilen: {spec.minimum} – {spec.maximum} · Varsayılan: {spec.default}{spec.integral?' · Tam sayı':''}</small>}</label>
          {!valid&&<div className="cmp-warning">2–5 farklı sayı gir. Her değer seçilen parametrenin geçerli aralığında olmalı.</div>}
          <div className="sens-numbers">
            <Numeric label="Ajan / referans sayısı" value={config.population_size} min={5} max={32} onChange={v=>update({population_size:Math.trunc(v)})}/>
            <Numeric label="Referans adımı" value={config.iterations} min={1} max={120} onChange={v=>update({iterations:Math.trunc(v)})}/>
            <Numeric label="Tohum / tekrar" value={config.trials} min={2} max={5} onChange={v=>update({trials:Math.trunc(v)})}/>
            <Numeric label="İlk tohum" value={config.seed_start} min={0} max={2147483642} onChange={v=>update({seed_start:Math.trunc(v)})}/>
            <Numeric label="Başarı eşiği" value={config.success_tolerance} min={.00000001} max={100} step={.0001} onChange={v=>update({success_tolerance:v})}/>
          </div>
          <div className="bmk-budget-note"><strong>{Number.isFinite(total)?total.toLocaleString('tr-TR'):'—'} toplam gerçek NFE</strong><span>{parsed.length} parametre değeri × {config.trials} tohum</span><span>Diğer parametreler karşılaştırma laboratuvarının varsayılan değerlerini kullanır.</span></div>
          {tooLarge&&<div className="cmp-warning">105.000 NFE sınırı aşıldı; değer, adım veya tekrar sayısını azalt.</div>}
          {stale&&result&&<div className="cmp-warning">Ayarlar değişti. Gösterilen sonuç önceki deneye aittir.</div>}
          <button className="button-primary bmk-run" disabled={loading||!valid||tooLarge||!catalog||!Object.keys(specs).length} onClick={start}>
            {loading?<span className="spinner"/>:<Play size={16} fill="currentColor"/>}{loading?'Duyarlılık deneyi çalışıyor…':'Duyarlılığı analiz et'}</button>
        </div>
      </section>
      <div className="sens-main">
        {error&&<div role="alert" className="cmp-alert">{error}<button aria-label="Hatayı kapat" onClick={()=>setError(null)}>×</button></div>}
        {result? <>
          <section className="sens-stats">
            <div className="bmk-kpi"><span>DEĞER SAYISI</span><strong>{result.groups.length}</strong><small>Parametre varyantı</small></div>
            <div className="bmk-kpi"><span>TOHUM / DEĞER</span><strong>{result.seeds.length}</strong><small>Ortak tohum etiketleri</small></div>
            <div className="bmk-kpi"><span>TOPLAM NFE</span><strong>{result.total_evaluations.toLocaleString('tr-TR')}</strong><small>Tüm bağımsız koşular</small></div>
            <div className="bmk-kpi"><span>EN DÜŞÜK ORT. HATA</span><strong>{fmt(winner?.mean_error??0)}</strong><small>{result.parameters.parameter} = {winner?.parameter_value} (yalnızca bu deney)</small></div>
          </section>
          <section className="panel sens-chart-panel"><div className="panel-heading"><div><span className="label-overline">02 / YAKINSAMA</span><h2>Parametre değerlerine göre ortalama hata</h2></div><Activity size={17}/></div><Curves result={result}/></section>
          <section className="panel"><div className="panel-heading"><div><span className="label-overline">03 / PARAMETRE ETKİSİ</span><h2>Varyant karşılaştırma tablosu</h2></div><div className="sens-actions"><button className="button-subtle" onClick={exportCsv}><ArrowDownToLine size={15}/> CSV</button>
            <button className="button-subtle" onClick={()=>downloadJson(result,`sensitivity-${result.sensitivity_id.slice(0,8)}.json`)}><ArrowDownToLine size={15}/> JSON</button></div></div>
            <div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>Parametre değeri</th><th>Ort. mutlak hata</th><th>Medyan hata</th><th>Std. sapma</th><th>Başarı</th><th>Ort. süre</th><th>NFE / koşu</th></tr></thead>
              <tbody>{result.groups.map((g,i)=><tr key={g.parameter_value}>
                <td><span className="sens-swatch" style={{background:COLORS[i]}}/>{g.parameter_value}{g===winner?' · en düşük ort. hata':''}</td>
                <td>{fmt(g.mean_error)}</td><td>{fmt(g.median_error)}</td><td>{fmt(g.std_error)}</td><td>%{Math.round(g.success_rate*100)}</td>
                <td>{fmt(g.mean_duration_ms,1)} ms</td><td>{result.evaluations_per_run.toLocaleString('tr-TR')}</td>
              </tr>)}</tbody></table></div>
          </section>
          <section className="panel"><div className="panel-heading"><div><span className="label-overline">04 / TEKRARLAR</span><h2>Tohum bazlı ham sonuçlar</h2></div></div>
            <div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>Parametre</th><th>Tohum</th><th>En iyi değer</th><th>Mutlak hata</th><th>İlk başarı NFE</th><th>Süre</th></tr></thead>
            <tbody>{result.groups.flatMap(g=>g.trials.map(t=><tr key={`${g.parameter_value}-${t.seed}`}><td>{g.parameter_value}</td><td>{t.seed}</td>
              <td>{fmt(t.best_value)}</td><td>{fmt(t.absolute_error)}</td><td>{t.first_success_nfe??'—'}</td><td>{fmt(t.duration_ms,1)} ms</td></tr>))}</tbody></table></div>
          </section>
          <div className="aco-science-note"><FlaskConical size={17}/><p>{result.methodology}</p></div>
        </>:<section className="panel sens-empty"><SlidersHorizontal size={28}/><h2>Parametre duyarlılığını keşfet</h2><p>Farklı değerlerin aynı probleme, aynı tohumlara ve tam aynı NFE bütçesine etkisini karşılaştır. Sonuçlar burada görünecek.</p></section>}
        <section className="panel"><div className="panel-heading"><div><span className="label-overline">05 / KALICI DENEY ARŞİVİ</span><h2>Önceki parametre deneyleri</h2></div>
          <button className="button-subtle" onClick={()=>{setShowHistory(!showHistory);if(!showHistory)void refresh()}}><Database size={16}/> Arşivi {showHistory?'gizle':`aç (${history.length})`}</button></div>
          {showHistory&&<div className="sens-history">{history.length?history.map(h=><div key={h.sensitivity_id} className="sens-history-row"><div><strong>{LABELS[h.algorithm]} · {h.parameter}</strong><small>{h.objective} · {h.values.join(' / ')} · {h.trials} tohum · {h.evaluations_per_run} NFE</small></div>
            <button className="button-subtle" disabled={loading} onClick={()=>open(h.sensitivity_id)}>Görüntüle</button></div>):<p>Henüz kayıtlı deney yok.</p>}</div>}
        </section>
      </div>
    </div>
  </div>;
}
