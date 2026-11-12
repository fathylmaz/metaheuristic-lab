import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownToLine, Database, FlaskConical, Play, Settings2 } from 'lucide-react';
import { runDimensional, getDimensionalHistory, openDimensional } from '../lib/api';
import { downloadCsv, downloadJson, numberFmt } from '../lib/math';
import type { DimensionalAlgorithm, DimensionalConfig, DimensionalResult, DimensionalGroup, SavedDimensional } from '../lib/types';

const COLORS:Record<DimensionalAlgorithm,string>={pso:'#70dfce',gwo:'#95bafb',de:'#f0c477',woa:'#ff9c8b',mfo:'#cf9efc',ssa:'#a9df7f',fa:'#ffba70',ba:'#f58e98',gsa:'#7ec5f8',abc:'#b1ed88',cs:'#c99de4',sma:'#b2a1f0',iwo:'#76ce9a',sa:'#fac17f'};
const LABELS:Record<DimensionalAlgorithm,string>={pso:'Parçacık Sürüsü (PSO)',gwo:'Gri Kurt (GWO)',de:'Diferansiyel Evrim (DE)',woa:'Balina (WOA)',mfo:'Güve-Alev (MFO)',ssa:'Salp Sürüsü (SSA)',fa:'Ateşböceği (FA)',ba:'Yarasa (BA)',gsa:'Yerçekimsel Arama (GSA)',abc:'Yapay Arı Kolonisi (ABC)',cs:'Guguk Kuşu (CS)',sma:'Cıvık Mantar (SMA)',iwo:'İstilacı Ot (IWO)',sa:'Tavlama (SA)'};
const INITIAL:DimensionalConfig={algorithms:['pso','gwo','de'],objective:'rastrigin',dimensions:10,
  population_size:24,iterations:90,trials:3,seed_start:42,success_tolerance:.001,
  pso_inertia_weight:.72,pso_cognitive_coefficient:1.49,pso_social_coefficient:1.49,pso_velocity_limit:.20,
  gwo_initial_a:2,de_mutation_factor:.75,de_crossover_rate:.90,
  woa_initial_a:2,woa_spiral_b:1,woa_spiral_probability:.5,mfo_spiral_b:1,ssa_c1_initial:2,
  fa_alpha:.18,fa_beta0:1,fa_gamma:.12,
  ba_min_frequency:0,ba_max_frequency:2,ba_initial_loudness:.9,
  ba_loudness_decay:.9,ba_initial_pulse_rate:.5,ba_pulse_growth:.9,
  gsa_initial_gravity:100,gsa_decay:20,gsa_epsilon:.01,
  abc_limit:30,cs_discovery_rate:.25,cs_step_scale:.08,cs_levy_exponent:1.5,
  sma_restart_probability:.03,iwo_max_population:60,iwo_min_seeds:0,iwo_max_seeds:5,
  iwo_sigma_initial:1.5,iwo_sigma_final:.02,iwo_modulation_index:3,
  sa_initial_temperature:10,sa_cooling_rate:.95,sa_step_scale:.10};
const formNumber=(v:number)=>numberFmt(v,5);
function Numeric({label,value,onChange,min,max,step=1}:{label:string;value:number;onChange:(v:number)=>void;min:number;max:number;step?:number}){
  return <label className="bmk-field"><span>{label}</span><input type="number" value={value} min={min} max={max} step={step} onChange={e=>{
    if(e.target.value==='')return;const x=Number(e.target.value);if(Number.isFinite(x))onChange(Math.max(min,Math.min(max,x)));
  }}/></label>;
}
function ErrorChart({result}:{result:DimensionalResult}){
  const width=760,height=255,left=56,right=20,top=16,bottom=39;
  const samples=result.groups[0]?.curve??[];
  if(!samples.length)return null;
  const logs=result.groups.flatMap(g=>g.curve.map(p=>Math.log10(Math.max(p.mean_error,1e-16))));
  const maximum=Math.max(1,...logs),minimum=Math.min(-1,...logs);
  const x=(n:number)=>left+(n-samples[0].evaluations)/Math.max(1,result.evaluations_per_run-samples[0].evaluations)*(width-left-right);
  const y=(v:number)=>top+(maximum-Math.log10(Math.max(1e-16,v)))/Math.max(1e-9,maximum-minimum)*(height-top-bottom);
  return <div className="sens-chart-wrap"><div className="sens-legend">{result.groups.map(g=><span key={g.algorithm}>
    <i style={{background:COLORS[g.algorithm]}}/>{LABELS[g.algorithm]}</span>)}</div>
    <svg className="sens-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Gerçek NFE bütçesine göre D boyutlu optimumdan ortalama hata">
      {[0,.25,.5,.75,1].map(k=><g key={k}><line x1={left} x2={width-right} y1={top+k*(height-top-bottom)} y2={top+k*(height-top-bottom)} stroke="#476372" opacity=".6" strokeDasharray="4 7"/>
        <text x={left-7} y={top+k*(height-top-bottom)+4} fill="#9fbdc7" fontSize="11" textAnchor="end">{Math.round(maximum-k*(maximum-minimum))}</text></g>)}
      {result.groups.map(g=><path key={g.algorithm} d={g.curve.map((p,i)=>`${i?'L':'M'}${x(p.evaluations).toFixed(2)},${y(p.mean_error).toFixed(2)}`).join(' ')}
        stroke={COLORS[g.algorithm]} strokeWidth="2.8" fill="none" strokeLinejoin="round"/>)}
      {[0,.25,.5,.75,1].map(k=><text key={k} x={left+k*(width-left-right)} y={height-17} fontSize="11" fill="#93b9c1" textAnchor="middle">
        {Math.round(samples[0].evaluations+k*(result.evaluations_per_run-samples[0].evaluations)).toLocaleString('tr-TR')}</text>)}
      <text x={width/2} y={height-2} fontSize="11" fill="#93b9c1" textAnchor="middle">Gerçek değerlendirme sayısı (NFE)</text>
      <text transform={`translate(13,${height/2}) rotate(-90)`} fontSize="11" fill="#93b9c1" textAnchor="middle">log₁₀ hata</text>
    </svg><p>Hatalar gerçek D-boyutlu amaç fonksiyonuyla hesaplanır. Yalnızca çizimde sıfır değerler 10⁻¹⁶ seviyesinde gösterilir.</p>
  </div>;
}
function Coordinates({group,dimension,objective}:{group:DimensionalGroup;dimension:number;objective:string}){
  const [seedIndex,setSeedIndex]=useState(0);
  const run=group.trials[Math.min(seedIndex,group.trials.length-1)];
  const points=run.trajectory;
  const width=350,height=250,pad=32;
  const limits:Record<string,number>={sphere:5.12,rastrigin:5.12,ackley:5,rosenbrock:3,griewank:6};
  const bound=limits[objective]??5.12;
  const fx=(v:number)=>pad+(v+bound)/(2*bound)*(width-2*pad);
  const fy=(v:number)=>height-pad-(v+bound)/(2*bound)*(height-2*pad);
  const trace=points.map((p,i)=>`${i?'L':'M'}${fx(p.best_position[0]).toFixed(2)},${fy(p.best_position[1]).toFixed(2)}`).join(' ');
  const last=run.best_position;
  const maxAbs=Math.max(.1,...last.map(v=>Math.abs(v)));
  return <section className="panel dim-inspect"><div className="panel-heading"><div><span className="label-overline">04 / ÇÖZÜMÜ İNCELE</span><h2>En iyi vektör ve ilk iki koordinat izdüşümü</h2></div><label className="bmk-field"><span>Temsili tohum</span><select value={seedIndex} onChange={e=>setSeedIndex(Number(e.target.value))}>
    {group.trials.map((t,i)=><option value={i} key={t.seed}>{group.algorithm.toUpperCase()} · {t.seed}</option>)}</select></label></div>
    <p className="bmk-section-note">İlk iki koordinat (<strong>x₁, x₂</strong>) yalnızca arşivlenen en iyi vektörün izdüşümüdür. {dimension} boyutlu optimizasyonun konumları ve uygunluk değerleri eksiksiz {dimension} bileşen üzerinden hesaplanmıştır.</p>
    <div className="dim-inspection-grid"><div className="dim-projection"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="En iyi D boyutlu çözümün x1-x2 düzlemine izdüşümü">
      {[0,.25,.5,.75,1].map(k=><g key={k}><line x1={pad+k*(width-2*pad)} x2={pad+k*(width-2*pad)} y1={pad} y2={height-pad} stroke="#486675" opacity=".35"/>
        <line y1={pad+k*(height-2*pad)} y2={pad+k*(height-2*pad)} x1={pad} x2={width-pad} stroke="#486675" opacity=".35"/></g>)}
      <line x1={fx(0)} x2={fx(0)} y1={pad} y2={height-pad} stroke="#7fb9bf" strokeDasharray="3 5" opacity=".5"/>
      <line y1={fy(0)} y2={fy(0)} x1={pad} x2={width-pad} stroke="#7fb9bf" strokeDasharray="3 5" opacity=".5"/>
      <path d={trace} fill="none" stroke={COLORS[group.algorithm]} strokeWidth="2" strokeLinejoin="round" opacity=".9"/>
      <circle cx={fx(points[0].best_position[0])} cy={fy(points[0].best_position[1])} r="4" fill="#ffb56b"/>
      <circle cx={fx(last[0])} cy={fy(last[1])} r="6" fill={COLORS[group.algorithm]} stroke="#e6ffff" strokeWidth="1.6"/>
      <text x={width-15} y={height-9} fill="#a6cbd0" fontSize="11" textAnchor="end">x₁</text>
      <text x="13" y="15" fill="#a6cbd0" fontSize="11">x₂</text>
    </svg><p>{group.algorithm.toUpperCase()} · Tohum {run.seed} · Son gerçek hata: <strong>{formNumber(run.best_error)}</strong></p></div>
    <div className="dim-vector-list" aria-label="D boyutlu gerçek en iyi vektörün bütün bileşenleri">
      {last.map((value,i)=><div key={i} className="dim-coordinate"><small>x{i+1}</small><div className="dim-coordinate-track"><i className="dim-zero"/><i className="dim-coordinate-bar" style={{left:value<0?`${50-49*Math.abs(value)/maxAbs}%`:'50%',width:`${49*Math.abs(value)/maxAbs}%`,background:COLORS[group.algorithm]}}/></div><strong title={String(value)}>{formNumber(value)}</strong></div>)}
    </div></div>
  </section>;
}
export default function DimensionalLab(){
  const [config,setConfig]=useState<DimensionalConfig>(INITIAL);
  const [result,setResult]=useState<DimensionalResult|null>(null);
  const [history,setHistory]=useState<SavedDimensional[]>([]);
  const [historyOpen,setHistoryOpen]=useState(false);
  const [selected,setSelected]=useState<DimensionalAlgorithm>('gwo');
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [stale,setStale]=useState(false);
  const budget=config.population_size*(config.iterations+1);
  const total=budget*config.trials*config.algorithms.length;
  const iwoValid=!config.algorithms.includes('iwo')||(config.iwo_max_population>=config.population_size&&config.iwo_min_seeds<=config.iwo_max_seeds&&config.iwo_sigma_final<=config.iwo_sigma_initial);
  const canRun=config.algorithms.length>=2&&config.algorithms.length<=4&&total<=160000&&config.ba_max_frequency>config.ba_min_frequency&&iwoValid;
  const update=(changes:Partial<DimensionalConfig>)=>{setConfig(prev=>({...prev,...changes}));setStale(true)};
  const refresh=()=>getDimensionalHistory().then(setHistory).catch(()=>{});
  useEffect(()=>{void refresh();},[]);
  const toggle=(algorithm:DimensionalAlgorithm)=>{
    if(!config.algorithms.includes(algorithm)&&config.algorithms.length>=4)return;
    if(config.algorithms.includes(algorithm)&&config.algorithms.length<=2)return;
    update({algorithms:config.algorithms.includes(algorithm)?config.algorithms.filter(a=>a!==algorithm):[...config.algorithms,algorithm]});
  };
  async function start(){if(!canRun)return;setLoading(true);setError(null);
    try{const r=await runDimensional(config);setResult(r);setStale(false);setSelected(r.groups[0].algorithm);void refresh();}
    catch(e){setError(e instanceof Error?e.message:'Deney başarısız');}finally{setLoading(false)}
  }
  async function load(id:string){setLoading(true);setError(null);
    try{const r=await openDimensional(id);setResult(r);setConfig({...INITIAL,...r.parameters});setSelected(r.groups[0].algorithm);setHistoryOpen(false);setStale(false);}
    catch(e){setError(e instanceof Error?e.message:'Kayıt açılamadı');}finally{setLoading(false)}
  }
  const current=useMemo(()=>result?.groups.find(g=>g.algorithm===selected)??result?.groups[0], [result,selected]);
  const best=result?.groups.reduce((a,b)=>b.mean_error<a.mean_error?b:a,result.groups[0]);
  const exportCsv=()=>{if(!result)return;downloadCsv(result.groups.flatMap(g=>g.trials.map(t=>({
    algorithm:g.algorithm,objective:result.parameters.objective,dimensions:result.parameters.dimensions,seed:t.seed,
    best_error:t.best_error,success:t.best_error<=result.parameters.success_tolerance?1:0,
    first_success_nfe:t.first_success_nfe??'',duration_ms:t.duration_ms,function_evaluations:t.function_evaluations,
    best_vector:JSON.stringify(t.best_position)}))),`dimensional-${result.experiment_id.slice(0,8)}.csv`)};
  return <div className="dim-lab">
    <div className="cmp-intro panel"><div className="cmp-intro-icon"><FlaskConical size={22}/></div><div><strong>Gerçek yüksek boyutlu optimizasyon</strong><p>2, 5, 10, 30 boyutta gerçek vektörler; eşit NFE, çoklu tohum, yakınsama ve koordinat analizi. PSO, GWO, DE, WOA, MFO, SSA, FA, BA, GSA, ABC, CS, SMA, IWO ve SA.</p></div><div className="cmp-budget"><span>GERÇEK NFE / KOŞU</span><strong>{budget.toLocaleString('tr-TR')}</strong></div></div>
    <div className="dim-layout">
      <section className="panel dim-controls"><div className="panel-heading"><div><span className="label-overline">01 / DENEY TASARIMI</span><h2>Boyutlu deney ayarları</h2></div><Settings2 size={18}/></div>
        <div className="dim-fields"><div className="bmk-select-group"><strong>ALGORİTMALAR · 2–4 SEÇİM</strong>{(['pso','gwo','de','woa','mfo','ssa','fa','ba','gsa','abc','cs','sma','iwo','sa'] as DimensionalAlgorithm[]).map(a=><label key={a} className="bmk-check"><input type="checkbox" checked={config.algorithms.includes(a)} disabled={(config.algorithms.length<=2&&config.algorithms.includes(a))||(config.algorithms.length>=4&&!config.algorithms.includes(a))} onChange={()=>toggle(a)}/><span><i className="bmk-color" style={{background:COLORS[a]}}/>{LABELS[a]}</span></label>)}</div>
          <label className="bmk-field"><span>Amaç fonksiyonu</span><select value={config.objective} onChange={e=>update({objective:e.target.value as DimensionalConfig['objective']})}>
            {(['sphere','rastrigin','ackley','rosenbrock','griewank'] as const).map(o=><option key={o} value={o}>{o[0].toUpperCase()+o.slice(1)}</option>)}</select></label>
          <label className="bmk-field"><span>Gerçek boyut sayısı (D)</span><select value={config.dimensions} onChange={e=>update({dimensions:Number(e.target.value) as DimensionalConfig['dimensions']})}>
            {[2,5,10,30].map(d=><option key={d} value={d}>{d} boyut</option>)}</select></label>
          <div className="sens-numbers"><Numeric label="Ajan sayısı" value={config.population_size} min={8} max={64} onChange={v=>update({population_size:Math.round(v)})}/>
            <Numeric label="İterasyon" value={config.iterations} min={5} max={200} onChange={v=>update({iterations:Math.round(v)})}/>
            <Numeric label="Tekrar / tohum" value={config.trials} min={2} max={20} onChange={v=>update({trials:Math.round(v)})}/>
            <Numeric label="İlk tohum" value={config.seed_start} min={0} max={2147483640} onChange={v=>update({seed_start:Math.round(v)})}/>
            <Numeric label="Başarı eşiği" value={config.success_tolerance} min={.00000001} max={100} step={.0001} onChange={v=>update({success_tolerance:v})}/></div>
          <details className="dim-advanced"><summary>Algoritmaya özgü parametreler</summary><div className="dim-parameter-grid">
            {config.algorithms.includes('pso') && <Numeric label="PSO atalet w" value={config.pso_inertia_weight} min={0} max={1.2} step={.01} onChange={v=>update({pso_inertia_weight:v})}/>}
            {config.algorithms.includes('pso') && <Numeric label="PSO bilişsel c₁" value={config.pso_cognitive_coefficient} min={0} max={4} step={.01} onChange={v=>update({pso_cognitive_coefficient:v})}/>}
            {config.algorithms.includes('pso') && <Numeric label="PSO sosyal c₂" value={config.pso_social_coefficient} min={0} max={4} step={.01} onChange={v=>update({pso_social_coefficient:v})}/>}
            {config.algorithms.includes('pso') && <Numeric label="PSO hız sınırı" value={config.pso_velocity_limit} min={.01} max={1} step={.01} onChange={v=>update({pso_velocity_limit:v})}/>}
            {config.algorithms.includes('gwo') && <Numeric label="GWO başlangıç a₀" value={config.gwo_initial_a} min={.25} max={3} step={.05} onChange={v=>update({gwo_initial_a:v})}/>}
            {config.algorithms.includes('de') && <Numeric label="DE mutasyon F" value={config.de_mutation_factor} min={0} max={2} step={.05} onChange={v=>update({de_mutation_factor:v})}/>}
            {config.algorithms.includes('de') && <Numeric label="DE çaprazlama CR" value={config.de_crossover_rate} min={0} max={1} step={.05} onChange={v=>update({de_crossover_rate:v})}/>}
            {config.algorithms.includes('woa') && <Numeric label="WOA başlangıç a₀" value={config.woa_initial_a} min={.25} max={3} step={.05} onChange={v=>update({woa_initial_a:v})}/>}
            {config.algorithms.includes('woa') && <Numeric label="WOA spiral b" value={config.woa_spiral_b} min={.1} max={3} step={.05} onChange={v=>update({woa_spiral_b:v})}/>}
            {config.algorithms.includes('woa') && <Numeric label="WOA spiral olasılığı" value={config.woa_spiral_probability} min={0} max={1} step={.05} onChange={v=>update({woa_spiral_probability:v})}/>}
            {config.algorithms.includes('mfo') && <Numeric label="MFO spiral b" value={config.mfo_spiral_b} min={.1} max={3} step={.05} onChange={v=>update({mfo_spiral_b:v})}/>}
            {config.algorithms.includes('ssa') && <Numeric label="SSA başlangıç c₁" value={config.ssa_c1_initial} min={.25} max={3} step={.05} onChange={v=>update({ssa_c1_initial:v})}/>}
            {config.algorithms.includes('fa') && <Numeric label="FA rastgele adım α" value={config.fa_alpha} min={0} max={1} step={.01} onChange={v=>update({fa_alpha:v})}/>}
            {config.algorithms.includes('fa') && <Numeric label="FA başlangıç çekim β₀" value={config.fa_beta0} min={0} max={3} step={.05} onChange={v=>update({fa_beta0:v})}/>}
            {config.algorithms.includes('fa') && <Numeric label="FA ışık sönüm γ" value={config.fa_gamma} min={0} max={5} step={.01} onChange={v=>update({fa_gamma:v})}/>}
            {config.algorithms.includes('ba') && <Numeric label="BA en düşük frekans" value={config.ba_min_frequency} min={0} max={5} step={.05} onChange={v=>update({ba_min_frequency:v})}/>}
            {config.algorithms.includes('ba') && <Numeric label="BA en yüksek frekans" value={config.ba_max_frequency} min={0.05} max={5} step={.05} onChange={v=>update({ba_max_frequency:v})}/>}
            {config.algorithms.includes('ba') && <Numeric label="BA başlangıç ses şiddeti" value={config.ba_initial_loudness} min={.01} max={1} step={.05} onChange={v=>update({ba_initial_loudness:v})}/>}
            {config.algorithms.includes('ba') && <Numeric label="BA ses şiddeti sönümü" value={config.ba_loudness_decay} min={.01} max={1} step={.05} onChange={v=>update({ba_loudness_decay:v})}/>}
            {config.algorithms.includes('ba') && <Numeric label="BA en yüksek darbe oranı" value={config.ba_initial_pulse_rate} min={0} max={1} step={.05} onChange={v=>update({ba_initial_pulse_rate:v})}/>}
            {config.algorithms.includes('ba') && <Numeric label="BA darbe artışı γ" value={config.ba_pulse_growth} min={.05} max={5} step={.05} onChange={v=>update({ba_pulse_growth:v})}/>}
            {config.algorithms.includes('gsa') && <Numeric label="GSA ilk çekim G₀" value={config.gsa_initial_gravity} min={.01} max={500} step={1} onChange={v=>update({gsa_initial_gravity:v})}/>}
            {config.algorithms.includes('gsa') && <Numeric label="GSA sönüm α" value={config.gsa_decay} min={0} max={40} step={1} onChange={v=>update({gsa_decay:v})}/>}
            {config.algorithms.includes('gsa') && <Numeric label="GSA mesafe yumuşatma ε" value={config.gsa_epsilon} min={.001} max={1} step={.001} onChange={v=>update({gsa_epsilon:v})}/>}
            {config.algorithms.includes('abc') && <Numeric label="ABC terk etme limiti" value={config.abc_limit} min={1} max={200} onChange={v=>update({abc_limit:v})}/>}
            {config.algorithms.includes('cs') && <Numeric label="CS keşif/terk oranı" value={config.cs_discovery_rate} min={0} max={1} step={.05} onChange={v=>update({cs_discovery_rate:v})}/>}
            {config.algorithms.includes('cs') && <Numeric label="CS Lévy adım ölçeği" value={config.cs_step_scale} min={.001} max={.5} step={.01} onChange={v=>update({cs_step_scale:v})}/>}
            {config.algorithms.includes('cs') && <Numeric label="CS Lévy üssü β" value={config.cs_levy_exponent} min={1.1} max={1.9} step={.05} onChange={v=>update({cs_levy_exponent:v})}/>}
            {config.algorithms.includes('sma') && <Numeric label="SMA yeniden başlangıç z" value={config.sma_restart_probability} min={0} max={1} step={.01} onChange={v=>update({sma_restart_probability:v})}/>}
            {config.algorithms.includes('iwo') && <Numeric label="IWO en büyük koloni" value={config.iwo_max_population} min={8} max={128} onChange={v=>update({iwo_max_population:v})}/>}
            {config.algorithms.includes('iwo') && <Numeric label="IWO minimum tohum" value={config.iwo_min_seeds} min={0} max={8} onChange={v=>update({iwo_min_seeds:v})}/>}
            {config.algorithms.includes('iwo') && <Numeric label="IWO maksimum tohum" value={config.iwo_max_seeds} min={1} max={8} onChange={v=>update({iwo_max_seeds:v})}/>}
            {config.algorithms.includes('iwo') && <Numeric label="IWO ilk yayılma σ₀" value={config.iwo_sigma_initial} min={.01} max={5} step={.01} onChange={v=>update({iwo_sigma_initial:v})}/>}
            {config.algorithms.includes('iwo') && <Numeric label="IWO son yayılma σₛ" value={config.iwo_sigma_final} min={.01} max={5} step={.01} onChange={v=>update({iwo_sigma_final:v})}/>}
            {config.algorithms.includes('iwo') && <Numeric label="IWO azalma üssü" value={config.iwo_modulation_index} min={.1} max={6} step={.1} onChange={v=>update({iwo_modulation_index:v})}/>}
            {config.algorithms.includes('sa') && <Numeric label="SA başlangıç sıcaklığı T₀" value={config.sa_initial_temperature} min={.1} max={100} step={.1} onChange={v=>update({sa_initial_temperature:v})}/>}
            {config.algorithms.includes('sa') && <Numeric label="SA soğutma oranı r" value={config.sa_cooling_rate} min={.01} max={1} step={.01} onChange={v=>update({sa_cooling_rate:v})}/>}
            {config.algorithms.includes('sa') && <Numeric label="SA komşu adım σ" value={config.sa_step_scale} min={.01} max={1} step={.01} onChange={v=>update({sa_step_scale:v})}/>}
          </div></details>
          <div className="bmk-budget-note"><strong>{total.toLocaleString('tr-TR')} toplam NFE</strong><span>{config.algorithms.length} algoritma × {config.trials} tohum × {budget.toLocaleString('tr-TR')} değerlendirme · Her koşuda {config.dimensions} boyut</span></div>
          {!canRun&&<p className="cmp-warning">İki ile dört algoritma seç; toplam NFE en fazla 160.000 olmalı; BA frekans ve IWO popülasyon/tohum/σ sınırları geçerli olmalı.</p>}
          {config.algorithms.some(a=>['abc','cs','iwo','sa'].includes(a))&&<p className="bmk-section-note">ABC/CS/IWO/SA için her NFE kontrol noktası algoritmik nesil değildir. SA tek çözümle, IWO değişken sayıda bitkiyle çalışır. SA sıcaklığı ve IWO yayılımı NFE ilerlemesine göre normalize edilir.</p>}
          {stale&&<p className="cmp-warning">Ayarlar değiştirildi. Görünen sonuçlar önceki deneye ait.</p>}
          <button className="button-primary bmk-run" onClick={start} disabled={!canRun||loading}>{loading?<span className="spinner"/>:<Play size={15}/>} {loading?'Hesaplanıyor...':'Yüksek boyutlu deneyi başlat'}</button>
        </div></section>
      <div className="dim-main">
        {error&&<div className="alert-error" role="alert">{error}</div>}
        {!result?<section className="panel sens-empty"><Activity size={28}/><h2>Yüksek boyutlu araştırma alanı</h2><p>14 algoritmadan 2–4 tanesini gerçek D-boyutlu optimizasyon motorunda çalıştır. Tam vektörleri, NFE eğrilerini ve tekrar istatistiklerini incele.</p></section>:<>
          <div className="bmk-top-grid">
            <div className="bmk-kpi"><span>GERÇEK BOYUT</span><strong>{result.parameters.dimensions}D</strong><small>Her adayın koordinat sayısı</small></div>
            <div className="bmk-kpi"><span>ALGORİTMA</span><strong>{result.groups.length}</strong><small>Eşit gerçek değerlendirme</small></div>
            <div className="bmk-kpi"><span>TOPLAM NFE</span><strong>{result.total_evaluations.toLocaleString('tr-TR')}</strong><small>{result.evaluations_per_run.toLocaleString('tr-TR')} / koşu</small></div>
            <div className="bmk-kpi"><span>EN DÜŞÜK ORT. HATA</span><strong>{best?formNumber(best.mean_error):'—'}</strong><small>{best?.algorithm.toUpperCase()} · yalnızca bu deney</small></div>
          </div>
          <section className="panel"><div className="panel-heading"><div><span className="label-overline">02 / YAKINSAMA</span><h2>{result.parameters.dimensions} boyutta NFE bazlı ortalama hata</h2></div><Activity size={17}/></div><ErrorChart result={result}/></section>
          <section className="panel"><div className="panel-heading"><div><span className="label-overline">03 / KARŞILAŞTIRMA</span><h2>Algoritma özetleri</h2></div><div className="sens-actions"><button className="button-subtle" onClick={exportCsv}><ArrowDownToLine size={14}/> CSV</button><button className="button-subtle" onClick={()=>downloadJson(result,`dimensional-${result.experiment_id.slice(0,8)}.json`)}><ArrowDownToLine size={14}/> JSON</button></div></div>
            <div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>Algoritma</th><th>Ort. hata</th><th>Medyan</th><th>Std. sapma</th><th>Başarı</th><th>NFE / koşu</th></tr></thead><tbody>
              {result.groups.map(g=><tr key={g.algorithm}><td><i className="bmk-color" style={{background:COLORS[g.algorithm]}}/>{LABELS[g.algorithm]}</td><td>{formNumber(g.mean_error)}</td><td>{formNumber(g.median_error)}</td><td>{formNumber(g.std_error)}</td><td>%{Math.round(g.success_rate*100)}</td><td>{result.evaluations_per_run.toLocaleString('tr-TR')}</td></tr>)}
            </tbody></table></div><p className="bmk-section-note">Üç tohum veya daha az tekrar, genel istatistiksel üstünlük göstermez. Farklı algoritmalar aynı tohum etiketini kullanır; başlangıç popülasyonlarının özdeş olması garanti edilmez.</p></section>
          {current&&<div className="dim-detail-selector"><label className="bmk-field"><span>İzdüşümü ve tam vektörü incelenecek algoritma</span><select value={current.algorithm} onChange={e=>setSelected(e.target.value as DimensionalAlgorithm)}>
            {result.groups.map(g=><option value={g.algorithm} key={g.algorithm}>{LABELS[g.algorithm]}</option>)}</select></label></div>}
          {current&&<Coordinates key={`${result.experiment_id}-${current.algorithm}`} group={current} dimension={result.parameters.dimensions} objective={result.parameters.objective}/>}
          <section className="panel"><div className="panel-heading"><div><span className="label-overline">05 / TEKRARLAR</span><h2>Tohum bazlı sonuçlar</h2></div></div><div className="cmp-table-scroll"><table className="cmp-table"><thead><tr><th>Tohum</th>{result.groups.map(g=><th key={g.algorithm}>{g.algorithm.toUpperCase()} hata</th>)}<th>NFE / algoritma</th></tr></thead><tbody>
            {result.seeds.map((seed,i)=><tr key={seed}><td>{seed}</td>{result.groups.map(g=><td key={g.algorithm}>{formNumber(g.trials[i].best_error)}</td>)}<td>{result.evaluations_per_run.toLocaleString('tr-TR')}</td></tr>)}
          </tbody></table></div></section>
          <div className="method-note"><span className="note-spot"><FlaskConical size={14}/></span><div><strong>Matematiksel yöntem</strong><p>{result.methodology}</p></div></div>
        </>}
        <section className="panel"><div className="panel-heading"><div><span className="label-overline">06 / KALICI ARŞİV</span><h2>Yüksek boyutlu deneyler</h2></div><button className="button-subtle" onClick={()=>{setHistoryOpen(v=>!v);void refresh();}}><Database size={14}/> Arşiv aç ({history.length})</button></div>
          {historyOpen&&<div className="sens-history">{history.length===0?<p>Kaydedilmiş deney yok.</p>:history.map(h=><div key={h.experiment_id} className="sens-history-row"><div><strong>{h.objective.toUpperCase()} · {h.dimensions}D · {h.algorithms.map(a=>a.toUpperCase()).join(' + ')}</strong><small>{h.trials} tohum · {h.evaluations_per_run.toLocaleString('tr-TR')} NFE / koşu · {new Date(h.created_at).toLocaleString('tr-TR')}</small></div><button className="button-subtle" disabled={loading} onClick={()=>void load(h.experiment_id)}>Görüntüle</button></div>)}</div>}
        </section>
      </div>
    </div>
  </div>;
}
