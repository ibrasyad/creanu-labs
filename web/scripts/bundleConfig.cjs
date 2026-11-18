const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const configDir = path.resolve(__dirname, '../../config');

// 1. Read catalog.yaml
const catalogRaw = fs.readFileSync(path.join(configDir, 'catalog.yaml'), 'utf8');
const catalogDoc = yaml.load(catalogRaw);

// 2. Read date.yaml
const dateRaw = fs.readFileSync(path.join(configDir, 'date.yaml'), 'utf8');
const dateDoc = yaml.load(dateRaw);

// 3. Read event.yaml
const eventRaw = fs.readFileSync(path.join(configDir, 'event.yaml'), 'utf8');
const eventDoc = yaml.load(eventRaw);

// 4. Read funnel.yaml
const funnelRaw = fs.readFileSync(path.join(configDir, 'funnel.yaml'), 'utf8');
const funnelDoc = yaml.load(funnelRaw);

// 5. Read growth.yaml
const growthRaw = fs.readFileSync(path.join(configDir, 'growth.yaml'), 'utf8');
const growthDoc = yaml.load(growthRaw);

// 6. Read simulation.yaml
const simRaw = fs.readFileSync(path.join(configDir, 'simulation.yaml'), 'utf8');
const simDoc = yaml.load(simRaw);

// 7. Read tiers/
const tiersDir = path.join(configDir, 'tiers');
const tierFiles = fs.readdirSync(tiersDir).filter(f => f.endsWith('.yaml') && !f.startsWith('_'));
const tiersDoc = {};

for (const tf of tierFiles) {
  const content = fs.readFileSync(path.join(tiersDir, tf), 'utf8');
  const parsed = yaml.load(content);
  if (parsed && typeof parsed === 'object') {
    Object.assign(tiersDoc, parsed);
  }
}

// Assemble full comprehensive config
const fullConfig = {
  simulation: simDoc.simulation || simDoc,
  date: {
    start_date: "2026-01-01",
    end_date: "2026-03-31", // 90 days default!
    transaction_volume: dateDoc.date?.transaction_volume || dateDoc.transaction_volume || {},
  },
  catalog: catalogDoc.catalog || catalogDoc,
  funnel: funnelDoc.funnel || funnelDoc,
  growth: growthDoc.growth || growthDoc,
  event: eventDoc.event || eventDoc,
  tiers: tiersDoc,
};

const fullYaml = yaml.dump(fullConfig, { indent: 2, noArrayIndent: false, lineWidth: 140 });

const outPath = path.resolve(__dirname, '../src/engine/defaultConfig.ts');
const fileContent = `export const DEFAULT_CONFIG_YAML = ${JSON.stringify(fullYaml)};\n`;

fs.writeFileSync(outPath, fileContent, 'utf8');
console.log('Successfully bundled full configuration into defaultConfig.ts');
console.log('Catalog categories:', Object.keys(fullConfig.catalog).length);
console.log('Tiers count:', Object.keys(fullConfig.tiers).length);
console.log('Date range:', fullConfig.date.start_date, 'to', fullConfig.date.end_date);
