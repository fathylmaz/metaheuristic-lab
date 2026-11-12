import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownToLine, ArrowRight, BarChart3, CheckCircle2, Database, Pause, Play, RotateCcw, Settings2, ShieldCheck, SkipBack, SkipForward } from 'lucide-react';
import Landscape from './Landscape';
import { getComparisonHistory, openComparison, runComparison } from '../lib/api';
import { downloadCsv, downloadJson, numberFmt } from '../lib/math';
import type { Catalog, ComparisonConfig, ComparisonGroup, ComparisonResult, SavedComparison, ComparisonAlgorithm } from '../lib/types';
import { COMPARISON_DEFAULT_CONFIG } from '../lib/comparisonDefaults';

const ALGORITHMS: ComparisonAlgorithm[] = ['fa','pso','abc','mfo','gwo','woa','ba','ssa','sma','gsa','de','cs','iwo','sa'];
const names: Record<ComparisonAlgorithm,string> = {
  fa:'Ateşböceği (FA)', pso:'Parçacık Sürüsü (PSO)', abc:'Yapay Arı (ABC)',
  mfo:'Güve-Alev (MFO)', gwo:'Gri Kurt (GWO)', woa:'Balina (WOA)',
  ba:'Yarasa (BA)', ssa:'Salp Sürüsü (SSA)', sma:'Cıvık Mantar (SMA)',
  gsa:'Yerçekimsel Arama (GSA)', de:'Diferansiyel Evrim (DE)',
  cs:'Guguk Kuşu (CS)', iwo:'İstilacı Ot (IWO)', sa:'Tavlama (SA)',
};
const color: Record<ComparisonAlgorithm,string> = {
  fa:'#f5b46f', pso:'#6adbd0', abc:'#b6e890', mfo:'#e8a8da',
  gwo:'#95b9f5', woa:'#f4d27a', ba:'#e99b92', ssa:'#78d9af',
  sma:'#c3b1f5', gsa:'#68b7de', de:'#dfc883',
  cs:'#d9bbf2', iwo:'#9bc98e', sa:'#efb06c',
};
const MAX_SELECTION=6;
const INITIAL = COMPARISON_DEFAULT_CONFIG;
const readable=(n:number,precision=5)=>numberFmt(n,precision);

function Field({label,value,onChange,min,max,step=1}:{label:string;value:number;onChange:(n:number)=>void;min:number;max:number;step?:number}){
  return <label className="cmp-field"><span>{label}</span><input type="number" value={value} min={min} max={max} step={step}
    onChange={e=>{if(e.target.value==='')return;const num=Number(e.target.value);if(Number.isFinite(num))onChange(Math.max(min,Math.min(max,step===1?Math.trunc(num):num)));}}/></label>;
}

function MultiCurve({groups}:{groups:ComparisonGroup[]}){
  const width=940,height=250,left=65,right=30,top=20,bottom=40;
  const logs=groups.flatMap(g=>g.curve.map(p=>Math.log10(Math.max(1e-60,p.mean_best))));
  const hi=Math.ceil(Math.max(...logs)+.1),lo=Math.floor(Math.min(...logs)-.1);
  const low=lo===hi?lo-1:lo;
  const minNfe=groups[0].curve[0].evaluations;
  const maxNfe=groups[0].curve.at(-1)!.evaluations;
  const x=(v:number)=>left+(v-minNfe)/Math.max(1,maxNfe-minNfe)*(width-left-right);
  const y=(v:number)=>top+(hi-Math.log10(Math.max(1e-60,v)))/(hi-low)*(height-top-bottom);
  const path=(g:ComparisonGroup)=>g.curve.map((p,i)=>`${i?'L':'M'}${x(p.evaluations).toFixed(2)} ${y(p.mean_best).toFixed(2)}`).join(' ');
  return <div className="cmp-chart-wrap"><svg role="img" aria-label="Seçili algoritmaların NFE başına ortalama en iyi amaç değerlerinin logaritmik yakınsama eğrileri" className="cmp-curve-svg" viewBox={`0 0 ${width} ${height}`}>
    {Array.from({length:5},(_,i)=>{const v=hi-(hi-low)*i/4,yy=top+(height-top-bottom)*i/4;
      return <g key={i}><line x1={left} x2={width-right} y1={yy} y2={yy} stroke="#294551" strokeDasharray="5 6"/><text x={left-12} y={yy+4} fill="#92afba" fontSize="13" textAnchor="end">10^{v.toFixed(1)}</text></g>;})}
    {Array.from({length:5},(_,i)=>{const evals=Math.round(minNfe+(maxNfe-minNfe)*i/4);
      return <text key={i} x={x(evals)} y={height-10} textAnchor="middle" fontSize="12" fill="#91aeba">{evals.toLocaleString('tr-TR')}</text>;})}
    {groups.map(g=><path key={g.algorithm} d={path(g)} stroke={color[g.algorithm]} strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round"/>)}
    <text x={width/2} y={height-1} fontSize="11" textAnchor="middle" fill="#9cb3bc">Fonksiyon değerlendirmesi (NFE)</text>
  </svg><div className="cmp-chart-caption">Y ekseni log₁₀ ölçekli, sıfır değerler 10⁻⁶⁰ tabanında görüntülenir. NFE kontrol noktaları eşittir; ABC, CS, IWO ve SA için iç döngü sayıları farklı olabilir.</div></div>;
}

export default function ComparisonLab({catalog}:{catalog:Catalog|null}){
  const [config,setConfig]=useState<ComparisonConfig>(INITIAL);
  const [result,setResult]=useState<ComparisonResult|null>(null);
  const [history,setHistory]=useState<SavedComparison[]>([]);
  const [index,setIndex]=useState(0);
  const [playing,setPlaying]=useState(false);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [showVectors,setShowVectors]=useState(false);
  const [selected,setSelected]=useState<Partial<Record<ComparisonAlgorithm,number|null>>>({});
  const [advanced,setAdvanced]=useState(false);
  const [showHistory,setShowHistory]=useState(false);
  const [stale,setStale]=useState(false);
  const groups=useMemo(()=>result?.groups??[],[result]);
  const budget=config.population_size*(config.iterations+1);
  const lastIndex=(result?.groups[0]?.representative_run.frames.length??1)-1;
  const change=<K extends keyof ComparisonConfig>(key:K,value:ComparisonConfig[K])=>{setConfig(p=>({...p,[key]:value}));setStale(true);};
  const refreshHistory=()=>getComparisonHistory().then(setHistory).catch(e=>setError(e instanceof Error?e.message:'Kayıtlar alınamadı'));
  const selectedNames=config.algorithms.map(a=>a.toUpperCase()).join(' + ');

  useEffect(()=>{void refreshHistory()},[]);
  useEffect(()=>{
    if(!playing||!result)return;
    const timer=window.setInterval(()=>setIndex(prev=>{
      if(prev>=lastIndex){setPlaying(false);return lastIndex;}
      return prev+1;
    }),140);
    return ()=>window.clearInterval(timer);
  },[playing,result,lastIndex]);

  function toggleAlgorithm(algorithm:ComparisonAlgorithm){
    if(config.algorithms.includes(algorithm)){
      if(config.algorithms.length===2)return;
      change('algorithms',config.algorithms.filter(a=>a!==algorithm));
    }else if(config.algorithms.length<MAX_SELECTION){
      change('algorithms',ALGORITHMS.filter(a=>config.algorithms.includes(a)||a===algorithm));
    }
  }
  async function start(){
    setLoading(true);setError(null);setPlaying(false);
    try{
      const data=await runComparison(config);
      setResult(data);setIndex(0);setSelected({});setStale(false);
      setPlaying(true);void refreshHistory();
    }catch(e){setError(e instanceof Error?e.message:'İşlem başarısız');}
    finally{setLoading(false);}
  }
  async function load(id:string){
    setLoading(true);setError(null);setPlaying(false);
    try{
      const saved=await openComparison(id);
      setResult(saved);
      setConfig({...INITIAL,...saved.parameters,algorithms:saved.groups.map(g=>g.algorithm)});
      setIndex(0);setSelected({});setStale(false);setShowHistory(false);
    }catch(e){setError(e instanceof Error?e.message:'Kayıt açılamadı');}
    finally{setLoading(false);}
  }
  function exportCsv(){
    if(!result)return;
    downloadCsv(result.seeds.map((seed,i)=>{
      const row:Record<string,number>={seed, budget_nfe:result.evaluations_per_run};
      for(const g of result.groups){row[`${g.algorithm}_best`]=g.trials[i].best_value;
        row[`${g.algorithm}_duration_ms`]=g.trials[i].duration_ms;
        row[`${g.algorithm}_evaluations`]=g.trials[i].function_evaluations;}
      return row;
    }),`comparison-${result.comparison_id.slice(0,8)}.csv`);
  }
  return <div className="cmp-lab">
    <div className="cmp-intro panel"><div className="cmp-intro-icon"><BarChart3 size={24}/></div>
      <div><strong>Bilimsel karşılaştırma · 14 algoritmadan en fazla 6 seçim</strong><p>Seçilen sürekli optimizasyon algoritmaları aynı amaç fonksiyonunda ve tam eşit NFE bütçesinde çalışır. İkili testlerde eşleştirilmiş tohumlar ve Holm düzeltmesi kullanılır.</p></div>
      <div className="cmp-budget"><span>EŞİT HESAPLAMA BÜTÇESİ</span><strong>{budget.toLocaleString('tr-TR')} NFE / koşu</strong></div>
    </div>
    <div className="cmp-layout">
      <section className="panel cmp-controls"><div className="panel-heading"><div><span className="label-overline">01 / DENEY TASARIMI</span><h2>Karşılaştırma ayarları</h2></div><Settings2 size={18}/></div>
        <div className="cmp-control-body">
          <div className="cmp-algorithm-select"><span>ALGORİTMALAR · 2–6 SEÇİM ({config.algorithms.length}/6)</span>
            {ALGORITHMS.map(a=><label key={a} className="cmp-check-option"><input type="checkbox" checked={config.algorithms.includes(a)} disabled={config.algorithms.includes(a)?config.algorithms.length<=2:config.algorithms.length>=MAX_SELECTION} onChange={()=>toggleAlgorithm(a)}/><i style={{background:color[a]}}/>{names[a]}</label>)}
          </div>
          <label className="cmp-field"><span>AMAÇ FONKSİYONU</span><select value={config.objective} onChange={e=>change('objective',e.target.value)}>
            {(catalog?.objectives??[{id:'sphere',name:'Sphere'}]).map(o=><option key={o.id} value={o.id}>{o.name}</option>)}
          </select></label>
          <div className="cmp-fields-two"><Field label="Kaynak / ajan sayısı" value={config.population_size} min={5} max={40} onChange={v=>change('population_size',v)}/>
            <Field label="NFE referans adımı" value={config.iterations} min={1} max={150} onChange={v=>change('iterations',v)}/>
            <Field label="Tekrar / algoritma" value={config.trials} min={2} max={8} onChange={v=>change('trials',v)}/>
            <Field label="İlk rastgele tohum" value={config.seed_start} min={0} max={2147483639} onChange={v=>change('seed_start',v)}/></div>
          <Field label="Başarı eşiği (amaç ≤ değer)" value={config.success_tolerance} step={0.0001} min={0.000000001} max={100} onChange={v=>change('success_tolerance',v)}/>
          <button className="cmp-expand" onClick={()=>setAdvanced(v=>!v)} aria-expanded={advanced}>{advanced?'−':'+'} Algoritmaya özgü parametreler</button>
          {advanced&&<div className="cmp-advanced">
            <h4>FA parametreleri</h4><div className="cmp-fields-two"><Field label="Alpha" value={config.fa_alpha} min={0} max={1} step={.01} onChange={v=>change('fa_alpha',v)}/><Field label="Beta₀" value={config.fa_beta0} min={0} max={3} step={.05} onChange={v=>change('fa_beta0',v)}/><Field label="Gamma" value={config.fa_gamma} min={0} max={5} step={.01} onChange={v=>change('fa_gamma',v)}/></div>
            <h4>PSO parametreleri</h4><div className="cmp-fields-two"><Field label="Atalet (w)" value={config.pso_inertia_weight} min={0} max={1.2} step={.01} onChange={v=>change('pso_inertia_weight',v)}/><Field label="Bilişsel (c₁)" value={config.pso_cognitive_coefficient} min={0} max={4} step={.01} onChange={v=>change('pso_cognitive_coefficient',v)}/><Field label="Sosyal (c₂)" value={config.pso_social_coefficient} min={0} max={4} step={.01} onChange={v=>change('pso_social_coefficient',v)}/><Field label="Hız sınırı" value={config.pso_velocity_limit} min={.0001} max={1} step={.01} onChange={v=>change('pso_velocity_limit',v)}/></div>
            {config.algorithms.includes('abc')&&<><h4>ABC parametreleri</h4><div className="cmp-fields-two"><Field label="Terk etme limiti" value={config.abc_limit} min={1} max={500} onChange={v=>change('abc_limit',v)}/></div></>}
            {config.algorithms.includes('cs')&&<><h4>CS parametreleri</h4><div className="cmp-fields-two">
              <Field label="Terk oranı pₐ" value={config.cs_discovery_rate} min={0} max={1} step={.05} onChange={v=>change('cs_discovery_rate',v)}/>
              <Field label="Lévy adım ölçeği" value={config.cs_step_scale} min={.001} max={.5} step={.01} onChange={v=>change('cs_step_scale',v)}/>
              <Field label="Lévy üssü β" value={config.cs_levy_exponent} min={1.1} max={1.9} step={.05} onChange={v=>change('cs_levy_exponent',v)}/>
            </div></>}
            {config.algorithms.includes('iwo')&&<><h4>IWO parametreleri</h4><div className="cmp-fields-two">
              <Field label="Maks. bitki" value={config.iwo_max_population} min={5} max={100} onChange={v=>change('iwo_max_population',v)}/>
              <Field label="En az tohum" value={config.iwo_min_seeds} min={0} max={8} onChange={v=>change('iwo_min_seeds',v)}/>
              <Field label="En çok tohum" value={config.iwo_max_seeds} min={1} max={8} onChange={v=>change('iwo_max_seeds',v)}/>
              <Field label="İlk σ" value={config.iwo_sigma_initial} min={.01} max={10} step={.01} onChange={v=>change('iwo_sigma_initial',v)}/>
              <Field label="Son σ" value={config.iwo_sigma_final} min={.01} max={5} step={.01} onChange={v=>change('iwo_sigma_final',v)}/>
              <Field label="Azalma üssü" value={config.iwo_modulation_index} min={1} max={6} step={.1} onChange={v=>change('iwo_modulation_index',v)}/>
            </div></>}
            {config.algorithms.includes('sa')&&<><h4>SA parametreleri</h4><div className="cmp-fields-two">
              <Field label="Başlangıç sıcaklığı" value={config.sa_initial_temperature} min={.01} max={100} step={.1} onChange={v=>change('sa_initial_temperature',v)}/>
              <Field label="Soğutma r" value={config.sa_cooling_rate} min={.001} max={1} step={.01} onChange={v=>change('sa_cooling_rate',v)}/>
              <Field label="Komşu adım σ" value={config.sa_step_scale} min={.001} max={1} step={.01} onChange={v=>change('sa_step_scale',v)}/>
            </div></>}
            {config.algorithms.includes('mfo')&&<><h4>MFO parametreleri</h4><Field label="Spiral b" value={config.mfo_spiral_b} min={.1} max={3} step={.05} onChange={v=>change('mfo_spiral_b',v)}/></>}
            {config.algorithms.includes('gwo')&&<><h4>GWO parametreleri</h4><Field label="Başlangıç a₀" value={config.gwo_initial_a} min={.25} max={3} step={.05} onChange={v=>change('gwo_initial_a',v)}/></>}
            {config.algorithms.includes('woa')&&<><h4>WOA parametreleri</h4><div className="cmp-fields-two">
              <Field label="Başlangıç a₀" value={config.woa_initial_a} min={.25} max={3} step={.05} onChange={v=>change('woa_initial_a',v)}/>
              <Field label="Spiral b" value={config.woa_spiral_b} min={.1} max={3} step={.05} onChange={v=>change('woa_spiral_b',v)}/>
              <Field label="Spiral olasılığı" value={config.woa_spiral_probability} min={0} max={1} step={.05} onChange={v=>change('woa_spiral_probability',v)}/>
            </div></>}
            {config.algorithms.includes('ba')&&<><h4>BA parametreleri</h4><div className="cmp-fields-two">
              <Field label="En düşük frekans" value={config.ba_frequency_min} min={0} max={4} step={.1} onChange={v=>change('ba_frequency_min',v)}/>
              <Field label="En yüksek frekans" value={config.ba_frequency_max} min={.01} max={5} step={.1} onChange={v=>change('ba_frequency_max',v)}/>
              <Field label="İlk ses" value={config.ba_initial_loudness} min={.01} max={1} step={.05} onChange={v=>change('ba_initial_loudness',v)}/>
              <Field label="Ses azalması" value={config.ba_loudness_decay} min={.01} max={1} step={.05} onChange={v=>change('ba_loudness_decay',v)}/>
              <Field label="Darbe oranı" value={config.ba_initial_pulse_rate} min={0} max={1} step={.05} onChange={v=>change('ba_initial_pulse_rate',v)}/>
              <Field label="Darbe artışı" value={config.ba_pulse_growth} min={.01} max={5} step={.05} onChange={v=>change('ba_pulse_growth',v)}/>
            </div></>}
            {config.algorithms.includes('ssa')&&<><h4>SSA parametreleri</h4><Field label="İlk keşif c₁" value={config.ssa_c1_initial} min={.25} max={3} step={.05} onChange={v=>change('ssa_c1_initial',v)}/></>}
            {config.algorithms.includes('sma')&&<><h4>SMA parametreleri</h4><Field label="Yeniden başlangıç z" value={config.sma_restart_probability} min={0} max={1} step={.01} onChange={v=>change('sma_restart_probability',v)}/></>}
            {config.algorithms.includes('gsa')&&<><h4>GSA parametreleri</h4><div className="cmp-fields-two">
              <Field label="Başlangıç G₀" value={config.gsa_initial_gravity} min={.01} max={500} step={1} onChange={v=>change('gsa_initial_gravity',v)}/>
              <Field label="Sönüm α" value={config.gsa_decay} min={0} max={40} step={.5} onChange={v=>change('gsa_decay',v)}/>
              <Field label="Yumuşatma ε" value={config.gsa_epsilon} min={.000001} max={1} step={.001} onChange={v=>change('gsa_epsilon',v)}/>
            </div></>}
            {config.algorithms.includes('de')&&<><h4>DE parametreleri</h4><div className="cmp-fields-two">
              <Field label="Mutasyon F" value={config.de_mutation_factor} min={0} max={2} step={.05} onChange={v=>change('de_mutation_factor',v)}/>
              <Field label="Çaprazlama CR" value={config.de_crossover_rate} min={0} max={1} step={.05} onChange={v=>change('de_crossover_rate',v)}/>
            </div></>}

          </div>}
          <div className="cmp-seeds"><ShieldCheck size={16}/><span>Tohumlar: {Array.from({length:config.trials},(_,i)=>config.seed_start+i).join(', ')}</span></div>
          <div className="cmp-budget-note">14 sürekli algoritma karşılaştırılabilir. SA tek bir çözüm kullanır; IWO'nun popülasyonu değişir. CS/IWO/SA NFE uyarlamalı sürümlerle çalışır, ACO ise ayrı TSP problemidir. Seçilen tüm algoritmalar {budget.toLocaleString('tr-TR')} NFE'de durur; ABC döngü sayısı farklı olabilir.</div>
          {stale&&result&&<div className="cmp-warning">Ayarlar değiştirildi. Gösterilen sonuç önceki deneye aittir.</div>}
          <button className="button-primary cmp-run-btn" onClick={start} disabled={loading}>{loading?<span className="spinner"/>:<Play size={16} fill="currentColor"/>}{loading?'Algoritmalar çalıştırılıyor…':`${selectedNames} karşılaştırmasını başlat`}<ArrowRight size={16}/></button>
          <p className="cmp-footnote">{config.trials*config.algorithms.length} bağımsız koşu · Toplam {(budget*config.trials*config.algorithms.length).toLocaleString('tr-TR')} gerçek fonksiyon değerlendirmesi</p>
        </div>
      </section>
      <div className="cmp-main">
        {error&&<div className="cmp-alert" role="alert">{error}<button onClick={()=>setError(null)} aria-label="Hatayı kapat">×</button></div>}
        {result? <>
          <section className="cmp-score-grid">{groups.map(g=><div className="cmp-score-card" key={g.algorithm} style={{borderTopColor:color[g.algorithm]}}>
            <span className="cmp-score-label"><span className="cmp-dot" style={{background:color[g.algorithm]}}/>{names[g.algorithm]} · {result.trials_per_algorithm} koşu</span>
            <div className="cmp-score-main">{readable(g.mean_best,8)}<small>Ortalama en iyi amaç değeri</small></div>
            <div className="cmp-score-meta"><span>Medyan <b>{readable(g.median_best)}</b></span><span>Std. sapma <b>{readable(g.std_best)}</b></span><span>Başarı <b>%{(g.success_rate*100).toFixed(0)}</b></span></div>
          </div>)}</section>
          <section className="panel cmp-chart-panel"><div className="panel-heading"><div><span className="label-overline">02 / İSTATİSTİKSEL YAKINSAMA</span><h2>Eşit NFE bütçesinde performans</h2></div><span className="cmp-legend">{groups.map(g=><span key={g.algorithm}><i style={{background:color[g.algorithm]}}/>{g.algorithm.toUpperCase()}</span>)}</span></div><MultiCurve groups={groups}/></section>
          <section className="panel cmp-visual-panel"><div className="panel-heading"><div><span className="label-overline">03 / SENKRON HAREKET</span><h2>{groups.length} optimizasyon, aynı NFE çizelgesi</h2></div><label className="cmp-toggle"><input type="checkbox" checked={showVectors} onChange={e=>setShowVectors(e.target.checked)}/> Hız / yön çizgileri</label></div>
            <div className="cmp-visual-grid">{groups.map(g=><div key={g.algorithm} className="cmp-visual-cell"><div className="cmp-visual-head"><strong><i style={{background:color[g.algorithm]}}/>{names[g.algorithm]}</strong><span>Medyan koşu · seed {g.representative_run.seed}</span></div>
              <Landscape run={g.representative_run} frame={g.representative_run.frames[index]} objective={result.objective}
                selectedId={selected[g.algorithm]??null} setSelectedId={v=>setSelected(p=>({...p,[g.algorithm]:v}))} trails={true} showTargets={showVectors}/>
              <div className="cmp-visual-footer"><span>En iyi: <strong>{readable(g.representative_run.frames[index].best_so_far)}</strong></span><span>NFE {g.representative_run.frames[index].function_evaluations}</span></div>
            </div>)}</div>
            <div className="cmp-playback"><button aria-label="İlk kontrol noktasına dön" onClick={()=>{setPlaying(false);setIndex(0);}}><SkipBack size={17}/></button><button className="cmp-play" aria-label={playing?'Animasyonu durdur':'Animasyonu oynat'} onClick={()=>{if(index===lastIndex)setIndex(0);setPlaying(!playing);}}>{playing?<Pause size={16}/>:<Play size={16}/>}</button><button aria-label="Sonraki NFE adımı" onClick={()=>{setPlaying(false);setIndex(i=>Math.min(lastIndex,i+1));}}><SkipForward size={17}/></button>
              <div className="cmp-range"><span>NFE kontrol noktası {index} / {lastIndex} · {result.groups[0].representative_run.frames[index].function_evaluations.toLocaleString('tr-TR')} değerlendirme</span><input type="range" aria-label="Ortak NFE kontrol çizelgesi" min={0} max={lastIndex} value={index} onChange={e=>{setPlaying(false);setIndex(Number(e.target.value));}}/></div></div>
          </section>
          {!!result.pairwise?.length&&<section className="panel cmp-results-panel"><div className="panel-heading"><div><span className="label-overline">04 / EŞLEŞTİRİLMİŞ ANALİZ</span><h2>İkili karşılaştırma ve Holm düzeltmesi</h2></div></div>
            <p className="cmp-stats-note">A/B kazanımları, aynı tohum etiketindeki son en iyi değerlerden hesaplanır (daha küçük daha iyi). Fark, log₁₀(A) − log₁₀(B) medyanıdır; negatif değer A lehinedir. p değerleri keşifseldir, tek başına üstünlük kanıtı değildir. Az tekrar sayısında güçlü çıkarım yapılmaz.</p>
            <div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>İkili</th><th>A kazandı</th><th>B kazandı</th><th>Eşit</th><th>Medyan log₁₀ fark</th><th>p (ham)</th><th>p (Holm)</th></tr></thead><tbody>
              {result.pairwise.map(p=><tr key={`${p.algorithm_a}-${p.algorithm_b}`}><td>{p.algorithm_a.toUpperCase()} / {p.algorithm_b.toUpperCase()}</td><td>{p.a_wins}</td><td>{p.b_wins}</td><td>{p.ties}</td><td>{readable(p.median_log10_difference,3)}</td><td>{readable(p.p_value,4)}</td><td>{readable(p.p_holm,4)}</td></tr>)}
            </tbody></table></div>
          </section>}
          <section className="panel cmp-results-panel"><div className="panel-heading"><div><span className="label-overline">05 / TEKRARLANAN KOŞULAR</span><h2>Tohum bazında sonuçlar</h2></div><div className="cmp-export"><button onClick={exportCsv}><ArrowDownToLine size={15}/> CSV</button><button onClick={()=>downloadJson(result,`comparison-${result.comparison_id.slice(0,8)}.json`)}><ArrowDownToLine size={15}/> JSON</button></div></div>
            <div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>Tohum</th>{groups.map(g=><th key={g.algorithm}>{g.algorithm.toUpperCase()} · En iyi</th>)}{groups.map(g=><th key={g.algorithm}>{g.algorithm.toUpperCase()} · Süre</th>)}<th>NFE / algoritma</th></tr></thead>
              <tbody>{result.seeds.map((seed,i)=><tr key={seed}><td>{seed}</td>{groups.map(g=><td key={g.algorithm}>{readable(g.trials[i].best_value)}</td>)}{groups.map(g=><td key={g.algorithm}>{readable(g.trials[i].duration_ms,1)} ms</td>)}<td>{result.evaluations_per_run.toLocaleString('tr-TR')}</td></tr>)}</tbody></table></div>
          </section>
          <div className="cmp-method"><CheckCircle2 size={17}/><div><strong>Metodoloji</strong><p>{result.methodology} Kayıt kimliği: {result.comparison_id.slice(0,8)}.</p></div></div>
        </>:<div className="panel cmp-empty"><Activity size={31}/><h2>Karşılaştırmayı başlat</h2><p>14 algoritmadan 2–6 tanesini eşit gerçek fonksiyon değerlendirme bütçesinde çalıştır. Yakınsama, tohum bazlı sonuçlar ve keşifsel eşleştirilmiş istatistikler gerçek Python hesaplamalarından gelir.</p></div>}
        <section className="panel cmp-history"><div className="panel-heading"><div><span className="label-overline">06 / KALICI DENEY ARŞİVİ</span><h2>Kaydedilen karşılaştırmalar</h2></div><button className="cmp-history-toggle" onClick={()=>setShowHistory(v=>!v)}><Database size={15}/>{showHistory?'Gizle':`Arşivi aç (${history.length})`}</button></div>
          {showHistory&&<div className="cmp-history-body">{history.length?history.map(h=><div className="cmp-history-row" key={h.comparison_id}><div><strong>{h.objective.toUpperCase()} · {h.trials_per_algorithm} tekrar</strong><small>{new Date(h.created_at).toLocaleString('tr-TR')} · {h.evaluations_per_run.toLocaleString('tr-TR')} NFE / koşu · {Object.keys(h.mean_best).join(' + ').toUpperCase()}</small></div><button className="button-subtle" disabled={loading} onClick={()=>load(h.comparison_id)}><RotateCcw size={14}/> Yeniden aç</button></div>):<p>Henüz kaydedilmiş karşılaştırma yok.</p>}</div>}
        </section>
      </div>
    </div>
  </div>;
}
