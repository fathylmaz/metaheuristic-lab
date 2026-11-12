// Verify that npm resolved the actual Rollup WASM package, not its native binding.
'use strict';
const meta = require('rollup/package.json');
console.log('Rollup provider:', meta.name, '| version:', meta.version);
if (meta.name !== '@rollup/wasm-node') {
  console.error('ERROR: native Rollup is still selected; reinstall failed.');
  process.exit(2);
}
const bundler = require('rollup');
if (typeof bundler.rollup !== 'function') {
  console.error('ERROR: WASM Rollup API is not available.');
  process.exit(3);
}
console.log('WASM Rollup module loaded successfully.');
