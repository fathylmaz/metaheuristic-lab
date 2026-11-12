export function objectiveValue(id: string, x: number, y: number): number {
  if (id === 'sphere') return x*x + y*y;
  if (id === 'rastrigin') return 20 + x*x + y*y - 10*(Math.cos(2*Math.PI*x)+Math.cos(2*Math.PI*y));
  if (id === 'ackley') return -20*Math.exp(-0.2*Math.sqrt((x*x+y*y)/2)) - Math.exp((Math.cos(2*Math.PI*x)+Math.cos(2*Math.PI*y))/2) + 20 + Math.E;
  if (id === 'rosenbrock') return (1-x)**2 + 100*(y-x*x)**2;
  if (id === 'griewank') return 1 + (x*x+y*y)/4000 - Math.cos(x)*Math.cos(y/Math.sqrt(2));
  if (id === 'himmelblau') return (x*x+y-11)**2 + (x+y*y-7)**2;
  if (id === 'beale') return (1.5-x+x*y)**2 + (2.25-x+x*y*y)**2 + (2.625-x+x*y**3)**2;
  if (id === 'booth') return (x+2*y-7)**2 + (2*x+y-5)**2;
  return 0;
}
export function numberFmt(value: number, digits = 4) {
  if (!Number.isFinite(value)) return '—';
  if (Math.abs(value) < 0.0001 && value !== 0) return value.toExponential(2);
  return value.toLocaleString('tr-TR', { maximumFractionDigits: digits });
}
export function downloadJson(data: unknown, filename: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
  URL.revokeObjectURL(url);
}
export function downloadCsv(rows: Record<string, string | number | boolean | null | undefined>[], filename: string) {
  if (!rows.length) return;
  const keys = Object.keys(rows[0]);
  const esc = (value: string | number | boolean | null | undefined) => {
    const text = value == null ? '' : String(value);
    return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  };
  const text = [keys.map(esc).join(','), ...rows.map(row => keys.map(key => esc(row[key])).join(','))].join('\n');
  const url = URL.createObjectURL(new Blob(['\ufeff' + text], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
  URL.revokeObjectURL(url);
}
