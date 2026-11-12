import { useEffect, useState } from 'react';
import { BookOpenCheck, Download, ExternalLink, FileText, FlaskConical, RefreshCw, ShieldCheck } from 'lucide-react';
import { getReport, getReportHistory, reportUrl } from '../lib/api';
import type { ReportEntry, ScientificReport } from '../lib/types';

const kindName:Record<ReportEntry['kind'],string> = {
  comparison:'Karşılaştırma', benchmark:'Benchmark', sensitivity:'Parametre Duyarlılığı',
  dimensional:'Yüksek Boyut',
};

export default function ReportsLab(){
  const [entries,setEntries]=useState<ReportEntry[]>([]);
  const [current,setCurrent]=useState<ScientificReport|null>(null);
  const [selected,setSelected]=useState<string>('');
  const [loading,setLoading]=useState(true);
  const [opening,setOpening]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [kind,setKind]=useState<'all'|ReportEntry['kind']>('all');

  async function refresh(){
    setLoading(true);setError(null);
    try { setEntries(await getReportHistory()); }
    catch(e){setError(e instanceof Error?e.message:'Rapor arşivi yüklenemedi.');}
    finally{setLoading(false);}
  }
  useEffect(()=>{void refresh();},[]);

  async function open(entry:ReportEntry){
    setOpening(true);setError(null);setSelected(entry.kind+':'+entry.source_id);
    try {setCurrent(await getReport(entry.kind,entry.source_id));}
    catch(e){setError(e instanceof Error?e.message:'Deney raporu açılamadı.');setCurrent(null);}
    finally{setOpening(false);}
  }

  const filtered=kind==='all'?entries:entries.filter(e=>e.kind===kind);
  return <div className="report-lab">
    <div className="report-intro">
      <div className="report-intro-icon"><FileText size={22}/></div>
      <div><strong>Bilimsel raporlama · kayıtlı deneylerden, yeniden çalıştırmadan</strong>
        <p>Arşivden bir deney seç. Amaç, yöntem, NFE, ham sonuçlar, belirsizlik aralıkları ve eşleştirilmiş etki ölçüleri bir araya getirilsin.</p></div>
      <span className="report-intro-label">ARŞİV TABANLI</span>
    </div>
    <div className="report-layout">
      <section className="panel report-browser">
        <div className="panel-heading"><div><span className="label-overline">01 / KAYNAK DENEY</span><h2>Deney arşivi</h2></div>
          <button className="report-refresh" onClick={()=>void refresh()} disabled={loading} aria-label="Arşivi yenile"><RefreshCw size={17}/></button></div>
        <div className="report-browser-inner">
          <label className="bmk-field">Deney türü
            <select value={kind} onChange={e=>setKind(e.target.value as typeof kind)}>
              <option value="all">Tümü</option>
              <option value="comparison">Karşılaştırma</option>
              <option value="benchmark">Benchmark</option>
              <option value="sensitivity">Parametre Duyarlılığı</option>
              <option value="dimensional">Yüksek Boyut</option>
            </select>
          </label>
          <p className="report-microcopy">Son 20 kayıt listelenir. Kayıtları başka bir işlem başlatmadan raporlayabilirsin.</p>
          {loading?<div className="report-empty">Deney kayıtları yükleniyor…</div>:
            filtered.length===0?<div className="report-empty">Bu türde kayıtlı deney bulunamadı. Önce ilgili laboratuvarda bir deney çalıştır.</div>:
            <div className="report-entry-list">{filtered.map(entry=><button key={entry.kind+entry.source_id}
              className={'report-entry'+(selected===entry.kind+':'+entry.source_id?' selected':'')}
              onClick={()=>void open(entry)}>
                <strong>{kindName[entry.kind]}</strong>
                <small>{entry.description}</small><span>{entry.created_at.replace('T',' ').slice(0,19)} UTC</span>
              </button>)}</div>}
        </div>
      </section>
      <div className="report-main">
        {error&&<div className="report-error" role="alert">{error}</div>}
        {opening?<div className="panel report-placeholder"><FlaskConical size={24}/> Rapor oluşturuluyor…</div>:
          !current?<div className="panel report-placeholder"><BookOpenCheck size={35}/><strong>Bir kayıt seçerek başla</strong><p>Deney özeti, ham koşular, keşifsel bootstrap aralıkları ve varsa ikili etki testleri raporda görüntülenir.</p></div>:
          <>
            <div className="report-topline"><div><span className="label-overline">02 / ARAŞTIRMA RAPORU</span>
              <h2>{current.title}</h2><p>Kaynak kimliği: <code>{current.source_id}</code></p></div>
              <div className="report-buttons">
                <a href={reportUrl(current.source_kind,current.source_id,'html')} target="_blank" rel="noopener noreferrer" className="report-action primary"><ExternalLink size={15}/> Yazdır / PDF</a>
                <a href={reportUrl(current.source_kind,current.source_id,'md')} className="report-action"><Download size={15}/> Markdown</a>
                <a href={reportUrl(current.source_kind,current.source_id,'json')} download={`metaheuristic-${current.source_kind}-report.json`} className="report-action"><Download size={15}/> JSON</a>
              </div>
            </div>
            <div className="report-summary-grid">{current.highlights.map((line,i)=><div className="report-highlight" key={i}><span className="label-overline">{i===0?'DENEY KAPSAMI':'GÖZLENEN SONUÇ'}</span><strong>{line}</strong></div>)}</div>
            <section className="panel report-content">
              <div className="panel-heading"><div><span className="label-overline">03 / YÖNTEM</span><h2>Tekrarlanabilir deney bilgisi</h2></div><ShieldCheck size={19}/></div>
              <p>{current.methodology}</p>
              <div className="report-provenance"><span><b>Deney tarihi (UTC)</b> {current.experiment_created_at}</span>
                <span><b>Kaynak SHA-256</b> <code>{current.source_sha256}</code></span></div>
              <details className="report-parameters"><summary>Tam deney parametrelerini göster (JSON)</summary><pre>{JSON.stringify(current.parameters,null,2)}</pre></details>
            </section>
            {current.sections.map((sec,i)=><section className="panel report-content" key={sec.heading}>
              <div className="panel-heading"><div><span className="label-overline">{String(i+4).padStart(2,'0')} / SONUÇLAR</span><h2>{sec.heading}</h2></div></div>
              {sec.paragraphs.map((p,j)=><p key={j}>{p}</p>)}
              {sec.tables.map((table,j)=><div key={j} className="report-table-section">
                <h3>{table.caption}</h3><div className="report-table-scroll"><table><thead><tr>{table.headers.map((header,k)=><th key={k}>{header}</th>)}</tr></thead>
                <tbody>{table.rows.map((row,k)=><tr key={k}>{row.map((value,l)=><td key={l}>{value}</td>)}</tr>)}</tbody></table></div>
                <small>{table.rows.length} satır</small></div>)}
            </section>)}
            <section className="panel report-limitations"><span className="label-overline">ARAŞTIRMA SINIRLARI</span><h2>Bu sonuçlar nasıl yorumlanmalı?</h2>
              {current.caveats.map((note,i)=><p key={i}>{note}</p>)}</section>
            <p className="report-print-note">Yazdır / PDF seçeneği raporun baskıya uygun HTML sürümünü açar. Tarayıcıda Ctrl+P → “PDF olarak kaydet” ile PDF alabilirsin. Hiçbir algoritma tekrar çalıştırılmaz.</p>
          </>}
      </div>
    </div>
  </div>;
}
