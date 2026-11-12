/** Print the sizes of all emitted JavaScript bundles without changing the build. */
import { readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
const location = join(process.cwd(), 'dist', 'assets');
try {
  const names = (await readdir(location)).filter(name => name.endsWith('.js'));
  const files = await Promise.all(names.map(async name => ({name, bytes:(await stat(join(location,name))).size})));
  files.sort((a,b) => b.bytes - a.bytes);
  if (!files.length) throw new Error('dist/assets içinde JavaScript bulunamadı');
  const kb = bytes => (bytes/1000).toFixed(2);
  console.log('Metaheuristic Lab — JavaScript paket raporu');
  for(const file of files) console.log(`${kb(file.bytes).padStart(8)} KB   ${file.name}`);
  const total = files.reduce((sum,file) => sum+file.bytes,0);
  console.log(`Toplam: ${kb(total)} KB; en büyük parça: ${kb(files[0].bytes)} KB`);
  if (files[0].bytes > 500_000) console.warn('Not: En büyük parça 500 KB üzerinde; kod bölmeyi tekrar inceleyin.');
  else console.log('En büyük JavaScript parçası 500 KB altında.');
} catch(err) {
  console.error('Önce npm.cmd run build çalıştırmalısın:', err.message);
  process.exitCode = 1;
}
