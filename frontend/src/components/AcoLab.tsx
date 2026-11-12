import { useEffect, useMemo, useState, type ReactElement } from 'react';
import { Activity, ArrowDownToLine, ArrowRight, BookOpen, CheckCircle2, Clock3, FastForward, Info, Pause, Play, RotateCcw, Settings2, SkipBack, SkipForward, Waypoints } from 'lucide-react';
import { runAcoSimulation } from '../lib/api';
import { downloadCsv, downloadJson, numberFmt } from '../lib/math';
import type { AcoCity, AcoConfig, AcoFrame, AcoRun } from '../lib/types';

const DEFAULT: AcoConfig = {city_count:16,ant_count:24,iterations:80,alpha:1,beta:3,evaporation:.35,deposit_q:20,seed:42,city_seed:7,layout:'uniform'};
const pos = (city:AcoCity) => ({x:30 + city.x * 700,y:30 + city.y * 420});
const colors = {best:'#82f4d0', tour:'#f5b866', pheromone:'#5ba6db'};

function Slider({label,hint,value,min,max,step,change,decimals=2}: {label:string;hint:string;value:number;min:number;max:number;step:number;change:(n:number)=>void;decimals?:number}) {
  return <div className="field-group"><label className="field-top"><span>{label}<small>{hint}</small></span><strong>{value.toFixed(decimals)}</strong></label>
    <input type="range" aria-label={label} min={min} max={max} step={step} value={value} onChange={e=>change(Number(e.target.value))}/>
    <div className="field-range"><span>{min}</span><span>{max}</span></div></div>;
}

function pathPoints(route:number[], cities:AcoCity[]):string {
  return route.length ? [...route,route[0]].map(id=>{
    const c=cities[id];if(!c)return '';const p=pos(c);return `${p.x},${p.y}`;
  }).join(' ') : '';
}

function RouteMap({run,frame,selectedAnt,selectedCity,setSelectedCity,showPheromone,showTour,showBest}:
  {run:AcoRun;frame:AcoFrame;selectedAnt:number;selectedCity:number|null;setSelectedCity:(n:number|null)=>void;showPheromone:boolean;showTour:boolean;showBest:boolean}) {
  const maxTau=Math.max(...frame.pheromone.flat(),1e-10);
  const tour=frame.ant_tours[selectedAnt]??frame.ant_tours[0];
  const edges: ReactElement[]=[];
  for(let i=0;i<run.cities.length;i++)for(let j=i+1;j<run.cities.length;j++){
    const strength=frame.pheromone[i][j]/maxTau;
    if(strength<.09)continue;
    const a=pos(run.cities[i]),b=pos(run.cities[j]);
    edges.push(<line key={`${i}-${j}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
      stroke={colors.pheromone} strokeWidth={.5+4*Math.sqrt(strength)} opacity={.09+.46*Math.sqrt(strength)}/>);
  }
  return <div className="aco-map-area"><svg viewBox="0 0 760 480" role="img" aria-label="Şehirler, feromon yoğunlukları ve karıncaların kapalı rotaları">
    <defs><pattern id="aco-grid" width="38" height="38" patternUnits="userSpaceOnUse"><path d="M38 0H0V38" fill="none" stroke="#2e4b55" strokeWidth="1" opacity=".36"/></pattern></defs>
    <rect width="760" height="480" fill="#0c222c"/><rect width="760" height="480" fill="url(#aco-grid)"/>
    {showPheromone&&<g>{edges}</g>}
    {showTour&&tour&&<polyline points={pathPoints(tour.route,run.cities)} fill="none" stroke={colors.tour} strokeWidth="2.5" strokeDasharray="7 6" opacity=".85"/>}
    {showBest&&<polyline points={pathPoints(frame.best_route,run.cities)} fill="none" stroke={colors.best} strokeWidth="3.1" opacity=".93" strokeLinejoin="round"/>}
    {run.cities.map(city=>{const p=pos(city);return <g key={city.id} onClick={()=>setSelectedCity(selectedCity===city.id?null:city.id)} style={{cursor:'pointer'}}>
      <circle cx={p.x} cy={p.y} r={selectedCity===city.id?16:13} fill="#133c42" stroke={selectedCity===city.id?'#ffd47b':'#73d8c2'} strokeWidth={selectedCity===city.id?2.7:1.5}/>
      <circle cx={p.x} cy={p.y} r="8.3" fill={selectedCity===city.id?'#ffcc76':'#65d6bb'}/>
      <text x={p.x} y={p.y+3.5} textAnchor="middle" fontSize="10" fontWeight="800" fill="#0a2b31">{city.id+1}</text>
    </g>})}
    <g transform="translate(13 13)"><rect width="193" height="24" rx="5" fill="#0c1c29" stroke="#31515a"/><circle cx="13" cy="12" r="4" fill="#79e7c7"/><text x="25" y="16" fontSize="10" fill="#bdd8dd" fontWeight="600">AYRIK TSP · {run.cities.length} ŞEHİR</text></g>
  </svg></div>;
}

function AcoConvergence({run,index}:{run:AcoRun;index:number}) {
  const W=780,H=195,L=61,R=15,T=16,B=35;
  const best=run.frames.map(f=>f.best_length);const means=run.frames.map(f=>f.mean_length);
  const min=Math.min(...best)*.96,max=Math.max(...means)*1.04;
  const X=(i:number)=>L+i/Math.max(1,best.length-1)*(W-L-R);
  const Y=(v:number)=>T+(max-v)/(max-min||1)*(H-T-B);
  const curve=(values:number[],through:number)=>values.slice(0,through+1).map((v,i)=>`${i?'L':'M'}${X(i).toFixed(2)},${Y(v).toFixed(2)}`).join(' ');
  return <svg viewBox={`0 0 ${W} ${H}`} className="aco-curve-svg" role="img" aria-label="Tur uzunluğu yakınsama grafiği">
    {[0,.25,.5,.75,1].map(step=><g key={step}><line x1={L} x2={W-R} y1={T+step*(H-T-B)} y2={T+step*(H-T-B)} stroke="#2e5360" strokeDasharray="4 6"/><text x="5" y={T+step*(H-T-B)+4} fontSize="10" fill="#91aebb">{numberFmt(max-step*(max-min),2)}</text></g>)}
    <path d={curve(means,index)} fill="none" stroke="#edb36f" strokeWidth="2" opacity=".8"/>
    <path d={curve(best,index)} fill="none" stroke={colors.best} strokeWidth="3" strokeLinejoin="round"/>
    <line x1={X(index)} x2={X(index)} y1={T} y2={H-B} stroke="#83e9ca" strokeDasharray="2 5" opacity=".5"/>
    <circle cx={X(index)} cy={Y(best[index])} r="5" fill={colors.best}/>
    {[0,.25,.5,.75,1].map(k=><text key={k} x={X(Math.round(k*(best.length-1)))} y={H-10} fontSize="11" fill="#96aeb9" textAnchor="middle">{1+Math.round(k*(best.length-1))}</text>)}
  </svg>;
}

export default function AcoLab(){
  const [config,setConfig]=useState<AcoConfig>(DEFAULT);
  const [used,setUsed]=useState<AcoConfig|null>(null);
  const [run,setRun]=useState<AcoRun|null>(null);
  const [index,setIndex]=useState(0);
  const [selectedAnt,setSelectedAnt]=useState(0);
  const [selectedCity,setSelectedCity]=useState<number|null>(null);
  const [playing,setPlaying]=useState(false);
  const [speed,setSpeed]=useState(1);
  const [showPheromone,setShowPheromone]=useState(true);
  const [showTour,setShowTour]=useState(true);
  const [showBest,setShowBest]=useState(true);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const frame=run?.frames[index]??null;
  const stale=used!==null&&JSON.stringify(config)!==JSON.stringify(used);
  const tours=frame?.ant_tours??[];
  const selectedTour=tours[selectedAnt]??null;
  const cityInfo=useMemo(()=>run&&frame&&selectedCity!==null?{
    value:frame.pheromone[selectedCity].reduce((a,b)=>a+b,0),
    neighbors:frame.pheromone[selectedCity].map((v,i)=>({id:i,weight:v})).filter(e=>e.id!==selectedCity).sort((a,b)=>b.weight-a.weight).slice(0,3),
  }:null,[run,frame,selectedCity]);
  useEffect(()=>{
    const controller=new AbortController();
    runAcoSimulation(DEFAULT,controller.signal).then(result=>{setRun(result);setUsed({...DEFAULT});setIndex(0);setPlaying(true)}).catch(e=>{if(e.name!=='AbortError')setError(e.message)});
    return ()=>controller.abort();
  },[]);
  useEffect(()=>{
    if(!playing||!run)return;
    const timer=window.setInterval(()=>setIndex(prev=>{
      if(prev+1>=run.frames.length){setPlaying(false);return run.frames.length-1;}
      return prev+1;
    }),Math.round(170/speed));
    return ()=>window.clearInterval(timer);
  },[playing,run,speed]);
  const update=<K extends keyof AcoConfig>(key:K,value:AcoConfig[K])=>setConfig(prev=>({...prev,[key]:value}));
  const start=async()=>{
    setLoading(true);setError(null);setPlaying(false);
    try{
      const result=await runAcoSimulation(config);
      setRun(result);setUsed({...config});setIndex(0);setSelectedAnt(0);setSelectedCity(null);setPlaying(true);
    }catch(e){setError(e instanceof Error?e.message:'Beklenmeyen ACO hatası');}
    finally{setLoading(false)}
  };
  return <div className="aco-lab">
    <div className="aco-intro"><div className="aco-intro-icon"><Waypoints size={23}/></div><div><strong>Karınca Kolonisi · Ayrık Rota Laboratuvarı</strong><p>Simetrik Öklidyen Gezgin Satıcı Problemi (TSP) · Ant System (AS) · Kapalı Hamilton turu</p></div><div className="aco-kind">FA / PSO / ABC karşılaştırmasından ayrı</div></div>
    {error&&<div className="cmp-alert" role="alert"><span>{error}</span><button onClick={()=>setError(null)}>×</button></div>}
    <div className="aco-stats-grid">
      <div className="stat-card"><div className="stat-icon teal"><Waypoints size={19}/></div><span>EN İYİ TUR UZUNLUĞU</span><strong>{frame?numberFmt(frame.best_length,5):'—'}</strong><small>Başlangıç şehrine dönen kapalı rota</small></div>
      <div className="stat-card"><div className="stat-icon orange"><Activity size={19}/></div><span>DEĞERLENDİRİLEN TUR</span><strong>{frame?.tours_evaluated.toLocaleString('tr-TR')??'—'}</strong><small>Her karınca = 1 tam tur</small></div>
      <div className="stat-card"><div className="stat-icon blue"><Waypoints size={19}/></div><span>ŞEHİR / KARINCA</span><strong>{run?.cities.length??config.city_count} <span className="stat-unit">/ {run?.parameters.ant_count??config.ant_count}</span></strong><small>Her tur tüm şehirleri bir kez ziyaret eder</small></div>
      <div className="stat-card"><div className="stat-icon purple"><Activity size={19}/></div><span>FARKLI TUR SAYISI</span><strong>{frame?.unique_tours??'—'}</strong><small>Başlangıç ve ters yön eşdeğer kabul edilir</small></div>
    </div>
    <div className="aco-layout"><div className="aco-main">
      <section className="panel aco-map-panel"><div className="panel-heading"><div><span className="label-overline">01 / KOLONİ DAVRANIŞI</span><h2>Feromon ağı ve en kısa tur <span className="surface-pill">TSP Graph</span></h2></div><span className="aco-frame-count">DÖNGÜ {frame?.iteration??0} / {run?.frames.length??config.iterations}</span></div>
        <div className="aco-visual-options"><label><input type="checkbox" checked={showPheromone} onChange={e=>setShowPheromone(e.target.checked)}/> Feromon ağı</label><label><input type="checkbox" checked={showBest} onChange={e=>setShowBest(e.target.checked)}/> En iyi rota</label><label><input type="checkbox" checked={showTour} onChange={e=>setShowTour(e.target.checked)}/> Seçili karınca</label></div>
        {run&&frame?<RouteMap run={run} frame={frame} selectedAnt={selectedAnt} selectedCity={selectedCity} setSelectedCity={setSelectedCity} showPheromone={showPheromone} showTour={showTour} showBest={showBest}/>:<div className="aco-loading"><Activity size={24}/> Rota simülasyonu hazırlanıyor...</div>}
        <div className="aco-legend"><span><i style={{background:colors.pheromone}}/> Feromon (kalınlık ve opaklık)</span><span><i style={{background:colors.best}}/> Küresel en iyi</span><span><i style={{background:colors.tour}}/> Seçili karınca</span></div>
        <div className="aco-controls"><div className="transport-controls"><button className="icon-btn" disabled={!run} title="Başa al" onClick={()=>{setIndex(0);setPlaying(false)}}><SkipBack size={18}/></button><button className="play-btn" disabled={!run} title={playing?'Duraklat':'Oynat'} onClick={()=>{if(run&&index===run.frames.length-1)setIndex(0);setPlaying(!playing)}}>{playing?<Pause size={18} fill="currentColor"/>:<Play size={18} fill="currentColor"/>}</button><button className="icon-btn" disabled={!run} title="Sonraki döngü" onClick={()=>{setIndex(i=>Math.min((run?.frames.length??1)-1,i+1));setPlaying(false)}}><SkipForward size={18}/></button><button className="icon-btn" disabled={!run} title="Sona git" onClick={()=>{setIndex((run?.frames.length??1)-1);setPlaying(false)}}><FastForward size={18}/></button></div>
          <input className="aco-scrub" type="range" aria-label="ACO döngü zaman çizelgesi" min={0} max={Math.max(0,(run?.frames.length??1)-1)} value={index} onChange={e=>{setIndex(Number(e.target.value));setPlaying(false)}} disabled={!run}/>
          <select className="speed-select" value={speed} onChange={e=>setSpeed(Number(e.target.value))} aria-label="Oynatma hızı"><option value={.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option><option value={4}>4×</option></select>
        </div>
        <div className="aco-inspection"><div><label>İNCELEMEK İÇİN KARINCA SEÇ</label><select value={selectedAnt} onChange={e=>setSelectedAnt(Number(e.target.value))}>{tours.map(ant=><option key={ant.id} value={ant.id}>Karınca {ant.id+1} · {numberFmt(ant.length,4)}</option>)}</select></div><div><label>SEÇİLİ KARINCA TUR UZUNLUĞU</label><strong>{selectedTour?numberFmt(selectedTour.length,6):'—'}</strong></div><div><label>SEÇİLİ ŞEHİR</label><strong>{selectedCity===null?'Haritadan şehir seç':`Şehir ${selectedCity+1}`}</strong></div></div>
        {cityInfo&&<div className="aco-city-inspect"><strong>Şehir {selectedCity!+1} · Toplam feromon {numberFmt(cityInfo.value,4)}</strong><span>En güçlü bağlantılar: {cityInfo.neighbors.map(n=>`${n.id+1} (${numberFmt(n.weight,2)})`).join(' · ')}</span></div>}
      </section>
      <section className="panel aco-chart-panel"><div className="panel-heading"><div><span className="label-overline">02 / YAKINSAMA ANALİZİ</span><h2>Tur uzunluğu ve koloni ortalaması</h2></div><span className="aco-chart-key"><i style={{background:colors.best}}/> En iyi <i style={{background:colors.tour}}/> Ortalama</span></div>{run&&frame?<AcoConvergence run={run} index={index}/>:<div className="aco-loading">Yakınsama verisi bekleniyor...</div>}
        <div className="chart-bottom"><span><strong>İterasyon en iyi:</strong> {frame?numberFmt(frame.iteration_best,5):'—'}</span><span><strong>Ortalama:</strong> {frame?numberFmt(frame.mean_length,5):'—'}</span><span><strong>Süre:</strong> {run?`${numberFmt(run.duration_ms,1)} ms`:'—'}</span></div></section>
      <section className="panel aco-guide"><div className="panel-heading"><div><span className="label-overline">03 / MATEMATİKSEL YÖNTEM</span><h2>Karıncalar yeni yolu nasıl seçiyor?</h2></div><BookOpen size={20}/></div><div className="aco-guide-cards"><div><strong>Geçiş olasılığı</strong><code>P(i→j) ∝ τᵢⱼ^α × (1/dᵢⱼ)^β</code><p>Karınca ziyaret edilmemiş komşular arasından feromon ile mesafe bilgisini kullanarak seçim yapar.</p></div><div><strong>Feromon güncellemesi</strong><code>τᵢⱼ ← (1−ρ)τᵢⱼ + Σ Q/Lₖ</code><p>Buharlaşma ve tüm karıncaların kullandığı kenarlara bıraktığı feromon birlikte uygulanır.</p></div></div><div className="aco-science-note"><Info size={17}/> Bu sürüm klasik Ant System (AS) varyantıdır. Her tur kapalıdır; şehirler tekrarlanmaz. 2-opt yerel arama eklenmemiştir. TSP tur değerlendirmeleri, sürekli fonksiyonların NFE sayılarıyla doğrudan karşılaştırılmaz.</div></section>
    </div><aside className="aco-side"><section className="panel params-panel"><div className="panel-heading"><div><span className="label-overline">KONTROL MERKEZİ</span><h2>ACO parametreleri</h2></div><Settings2 size={19}/></div><div className="settings-body"><label className="select-label">ŞEHİR DAĞILIMI<select value={config.layout} onChange={e=>update('layout',e.target.value as AcoConfig['layout'])}><option value="uniform">Rastgele dağılmış şehirler</option><option value="circle">Dairesel yerleşim</option><option value="clusters">Kümeli yerleşim</option></select></label>
      <Slider label="Şehir sayısı" hint="TSP çizgesinin düğümleri" value={config.city_count} min={6} max={32} step={1} decimals={0} change={n=>update('city_count',n)}/>
      <Slider label="Karınca sayısı" hint="Her iterasyonda kurulan tur sayısı" value={config.ant_count} min={4} max={60} step={1} decimals={0} change={n=>update('ant_count',n)}/>
      <Slider label="Döngü sayısı" hint="Koloninin kaç kez tur kuracağı" value={config.iterations} min={1} max={150} step={1} decimals={0} change={n=>update('iterations',n)}/>
      <Slider label="Alfa (α)" hint="Feromon etkisi" value={config.alpha} min={0} max={5} step={.1} change={n=>update('alpha',n)}/>
      <Slider label="Beta (β)" hint="Kısa mesafeyi tercih etme etkisi" value={config.beta} min={0} max={8} step={.1} change={n=>update('beta',n)}/>
      <Slider label="Buharlaşma (ρ)" hint="Her döngüde azalan feromon oranı" value={config.evaporation} min={.01} max={.99} step={.01} change={n=>update('evaporation',n)}/>
      <Slider label="Feromon miktarı (Q)" hint="Tur uzunluğuna bölünen depozit" value={config.deposit_q} min={.1} max={100} step={.1} change={n=>update('deposit_q',n)} decimals={1}/>
      <div className="aco-seed-grid"><label>ALGORİTMA TOHUMU<input type="number" min={0} max={2147483647} value={config.seed} onChange={e=>update('seed',Math.max(0,Math.min(2147483647,Math.round(Number(e.target.value)||0))))}/></label><label>ŞEHİR YERLEŞİM TOHUMU<input type="number" min={0} max={2147483647} value={config.city_seed} onChange={e=>update('city_seed',Math.max(0,Math.min(2147483647,Math.round(Number(e.target.value)||0))))}/></label></div>
      <div className="aco-eval-note"><CheckCircle2 size={16}/> Planlanan tam tur değerlendirmesi: <b>{(config.ant_count*config.iterations).toLocaleString('tr-TR')}</b></div>
      {stale&&<div className="stale-warning"><RotateCcw size={14}/> Parametreler değişti, sonuçları yeniden hesapla.</div>}
      <button className="button-primary start-btn" onClick={start} disabled={loading}>{loading?<span className="spinner"/>:<Play size={17} fill="currentColor"/>}{loading?'Hesaplanıyor...':'ACO simülasyonunu çalıştır'}<ArrowRight size={16}/></button>
      <div className="output-actions"><button disabled={!run} onClick={()=>{if(run)downloadJson(run,`aco-tsp-${run.parameters.city_seed}-${run.parameters.seed}.json`)}}><ArrowDownToLine size={15}/> JSON</button><button disabled={!run} onClick={()=>{if(run)downloadCsv(run.frames.map(f=>({iteration:f.iteration,best_length:f.best_length,iteration_best:f.iteration_best,mean_length:f.mean_length,unique_tours:f.unique_tours,tours_evaluated:f.tours_evaluated})),`aco-tsp-${run.parameters.seed}.csv`)}}><ArrowDownToLine size={15}/> CSV</button></div>
      </div></section><div className="method-note"><span className="note-spot"><Clock3 size={13}/></span><div><strong>Ayrık optimizasyon modeli</strong><p>Şehirler iki boyutlu düzlemde gösterilir; motor her karıncanın gerçek turunu, tur uzunluğunu ve feromon matrisini hesaplayarak animasyona aktarır.</p></div></div></aside></div>
  </div>;
}
