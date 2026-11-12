import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, Database, Download, Gauge, RefreshCw, ShieldAlert, ShieldCheck } from 'lucide-react';
import { getDimensionalHistory, getScienceAudit } from '../lib/api';
import { downloadJson, numberFmt } from '../lib/math';
import type { SavedDimensional, ScienceAudit } from '../lib/types';

const fmt = (n: number, precision = 4) => numberFmt(n, precision);
const duration = (n: number) => `${fmt(n, 2)} ms`;

export default function ScienceLab() {
  const [archive, setArchive] = useState<SavedDimensional[]>([]);
  const [selected, setSelected] = useState('');
  const [audit, setAudit] = useState<ScienceAudit | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try { setArchive(await getDimensionalHistory()); }
    catch (err) { setError(err instanceof Error ? err.message : 'Deney arşivi okunamadı.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  async function inspect(id: string) {
    setBusy(true); setSelected(id); setAudit(null); setError(null);
    try { setAudit(await getScienceAudit(id)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Bilimsel denetim alınamadı.'); }
    finally { setBusy(false); }
  }

  const widest = audit ? Math.max(1, ...audit.groups.map(group => group.median_duration_ms)) : 1;
  return <div className="science-lab">
    <div className="report-intro">
      <div className="report-intro-icon"><ShieldCheck size={23}/></div>
      <div><strong>Bilimsel doğrulama · arşiv tutarlılığı ve ölçülmüş performans</strong>
        <p>Kayıtlı yüksek boyutlu bir deneyi seç. Çözüm vektörleri, NFE, yakınsama, başarı oranı ve koşu süreleri yeniden hesaplama yapılmadan denetlensin.</p></div>
      <span className="report-intro-label">OKUMA MODU</span>
    </div>
    <div className="science-layout">
      <section className="panel science-browser">
        <div className="panel-heading"><div><span className="label-overline">01 / KAYITLI DENEY</span><h2>Yüksek boyut arşivi</h2></div>
          <button className="report-refresh" aria-label="Bilimsel arşivi yenile" disabled={loading} onClick={() => void refresh()}><RefreshCw size={17}/></button></div>
        <div className="science-browser-body">
          {loading ? <p className="science-note">Deney kayıtları yükleniyor…</p> : archive.length === 0 ?
            <p className="science-note">Henüz yüksek boyutlu deney kaydı yok. Yüksek Boyut Laboratuvarı veya Deney Kuyruğu üzerinden bir deney oluştur.</p> :
            <div className="report-entry-list">{archive.map(entry => <button key={entry.experiment_id}
              className={'report-entry' + (selected === entry.experiment_id ? ' selected' : '')}
              onClick={() => void inspect(entry.experiment_id)}>
              <strong>{entry.objective.toUpperCase()} · {entry.dimensions}D · {entry.algorithms.length} algoritma</strong>
              <small>{entry.algorithms.map(x => x.toUpperCase()).join(' · ')} · {entry.trials} tohum · {fmt(entry.evaluations_per_run, 0)} NFE / koşu</small>
              <span>{entry.created_at.replace('T', ' ').slice(0, 19)} UTC</span>
            </button>)}</div>}
          <p className="science-note"><Database size={13}/> Kayıtlar değiştirilmez. Son 20 yüksek boyutlu deney listelenir.</p>
        </div>
      </section>
      <div className="science-main">
        {error && <div role="alert" className="report-error">{error}</div>}
        {busy ? <div className="panel report-placeholder"><Activity size={28}/> Kayıtlar denetleniyor…</div> :
          !audit ? <div className="panel report-placeholder"><Gauge size={30}/><strong>Bilimsel bir denetim seç</strong><p>Arşivden bir deney seçildiğinde matematiksel tutarlılık ve kaydedilmiş süre profili gösterilir.</p></div> : <>
            <div className="science-headline">
              <div><span className="label-overline">02 / DENEY DENETİMİ</span><h2>Bilimsel denetim sonuçları</h2><p>Deney ID: <code>{audit.experiment_id}</code></p></div>
              <button className="report-action primary" onClick={() => downloadJson(audit, `scientific-audit-${audit.experiment_id}.json`)}>
                <Download size={15}/> JSON indir
              </button>
            </div>
            <div className={'science-status ' + (audit.status === 'passed' ? 'ok' : 'attention')}>
              {audit.status === 'passed' ? <CheckCircle2 size={20}/> : <ShieldAlert size={20}/>}
              <div><strong>{audit.status === 'passed' ? 'Arşiv tutarlılığı doğrulandı' : 'Denetimde tutarsızlık bulundu'}</strong>
                <p>{audit.status === 'passed' ? 'Kontrol edilen kayıt, vektör, yakınsama ve değerlendirme bütçesi testlerinden geçti.' : 'Aşağıdaki veri tutarlılığı sorunlarını inceleyin; sonuçları bilimsel olarak kullanmayın.'}</p></div>
            </div>
            <div className="science-stats">
              <div><span>Boyut</span><strong>{audit.dimensions}D</strong></div>
              <div><span>Algoritmalar</span><strong>{audit.algorithm_count}</strong></div>
              <div><span>Tekrar / algoritma</span><strong>{audit.trials_per_algorithm}</strong></div>
              <div><span>Toplam NFE</span><strong>{fmt(audit.expected_total_evaluations, 0)}</strong></div>
            </div>
            {audit.issues.length > 0 && <section className="panel science-section"><h3><ShieldAlert size={17}/> Tutarlılık sorunları</h3>
              <ul>{audit.issues.map((issue, i) => <li key={i}>{issue}</li>)}</ul></section>}
            <section className="panel science-section"><h3><Gauge size={17}/> Kalite ve ölçülmüş süreler</h3>
              <p>Hata değeri küçüldükçe daha iyi. Süreler koşunun gerçekleştirildiği ortamda ölçülmüştür; makineler arası kıyaslama yapılmaz.</p>
              <div className="report-table-scroll"><table><thead><tr><th>Algoritma</th><th>Ortalama hata</th><th>%95 aralık</th><th>Başarı</th><th>Medyan süre</th><th>p95 süre</th><th>NFE</th></tr></thead><tbody>
                {audit.groups.map(group => <tr key={group.algorithm}><td><strong>{group.algorithm.toUpperCase()}</strong></td><td>{fmt(group.mean_error)}</td>
                  <td>{fmt(group.ci95_low)} – {fmt(group.ci95_high)}</td><td>{(group.success_rate * 100).toFixed(1)}%</td>
                  <td>{duration(group.median_duration_ms)}</td><td>{duration(group.p95_duration_ms)}</td><td>{fmt(group.nfe_per_run, 0)}</td></tr>)}</tbody></table></div>
              <h4>Ölçülmüş medyan koşu süreleri</h4>
              <div className="science-bars">{audit.groups.map(group => <div className="science-bar-row" key={group.algorithm}>
                <span>{group.algorithm.toUpperCase()}</span><div className="science-bar-track"><i style={{width:`${Math.max(1, group.median_duration_ms / widest * 100)}%`}}/></div>
                <strong>{duration(group.median_duration_ms)}</strong></div>)}</div>
            </section>
            <section className="panel science-section"><h3><Activity size={17}/> Aynı tohum etiketleriyle karşılaştırma</h3>
              <p>Tam iki yönlü işaret testi ve Holm düzeltmesi keşifseldir. Başlangıç durumlarının algoritmalar arasında özdeş olduğu varsayılmaz.</p>
              <div className="report-table-scroll"><table><thead><tr><th>Çift</th><th>n</th><th>A / B kazandı</th><th>Medyan log₁₀(A/B)</th><th>Holm p</th></tr></thead><tbody>
                {audit.paired_comparisons.map(group => <tr key={group.pair}><td>{group.pair}</td><td>{group.n}</td><td>{group.a_wins} / {group.b_wins}</td>
                  <td>{fmt(group.median_log10_ratio)}</td><td>{fmt(group.p_holm)}</td></tr>)}</tbody></table></div>
            </section>
            <section className="panel science-section science-caveats"><h3><ShieldAlert size={17}/> Yöntem ve sınırlamalar</h3>
              <ul>{audit.warnings.map((note, i) => <li key={i}>{note}</li>)}</ul>
              <p><strong>Kapsam:</strong> {audit.scope}</p>
            </section>
          </>}
      </div>
    </div>
  </div>;
}
