import React, { useState } from 'react';
import yaml from 'js-yaml';
import {
  Calendar,
  ShoppingBag,
  GitFork,
  Sliders,
  ChevronDown,
  ChevronUp,
  Dices,
  Layers,
  Sparkles,
  Megaphone,
  TrendingUp,
  Plus,
  Trash2,
  Clock,
  Zap,
} from 'lucide-react';
import { ThemeConfig } from '../types/theme';

interface ConfigEditorProps {
  yamlContent: string;
  onChangeYaml: (val: string) => void;
  theme: ThemeConfig;
}

const MONTHS = [
  'january',
  'february',
  'march',
  'april',
  'may',
  'june',
  'july',
  'august',
  'september',
  'october',
  'november',
  'december',
];

const FUNNEL_STEPS = ['landing_page', 'product_view', 'add_to_cart', 'checkout', 'paid'];

export const ConfigEditor: React.FC<ConfigEditorProps> = ({
  yamlContent,
  onChangeYaml,
  theme,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeAdvancedTab, setActiveAdvancedTab] = useState<'tiers' | 'catalog' | 'funnel' | 'events' | 'growth'>('tiers');
  const [selectedTimingTier, setSelectedTimingTier] = useState('');

  // Parse YAML for structured controls
  let parsedConfig: any = null;
  let parseError: string | null = null;
  try {
    parsedConfig = yaml.load(yamlContent);
  } catch (err: any) {
    parseError = err.message;
  }

  // Update deep nested field helper
  const updateField = (path: string[], value: any) => {
    try {
      const cloned = JSON.parse(JSON.stringify(parsedConfig || {}));
      let target = cloned;
      for (let i = 0; i < path.length - 1; i++) {
        if (!target[path[i]]) target[path[i]] = {};
        target = target[path[i]];
      }
      target[path[path.length - 1]] = value;
      onChangeYaml(yaml.dump(cloned));
    } catch (err) {
      console.error('Failed to update config field:', err);
    }
  };

  // Quick Date Presets (7d, 14d, 30d, 90d)
  const setQuickDateRange = (days: number) => {
    const start = new Date(parsedConfig?.date?.start_date || '2026-01-01');
    const end = new Date(start);
    end.setDate(start.getDate() + days - 1);
    const endStr = end.toISOString().slice(0, 10);
    updateField(['date', 'end_date'], endStr);
  };

  // Roll new seed
  const rollRandomSeed = () => {
    const newSeed = Math.floor(10000000 + Math.random() * 90000000);
    updateField(['simulation', 'random_seed'], newSeed);
  };

  // Generic object mutation helpers (add / remove / rename keys)
  const mutateConfig = (mutator: (cfg: any) => void) => {
    try {
      const cloned = JSON.parse(JSON.stringify(parsedConfig || {}));
      mutator(cloned);
      onChangeYaml(yaml.dump(cloned));
    } catch (err) {
      console.error('Failed to mutate config:', err);
    }
  };

  const addMarketingEvent = () => {
    mutateConfig((cfg) => {
      cfg.event = cfg.event || {};
      let idx = Object.keys(cfg.event).length + 1;
      let key = `campaign_${idx}`;
      while (cfg.event[key]) key = `campaign_${++idx}`;
      cfg.event[key] = {
        name: 'New Campaign',
        description: 'Describe the campaign goal',
        year: 1,
        start_month: 1,
        end_month: 3,
        overall: { new_user: 1.1, visit: 1.1 },
      };
    });
  };

  const removeMarketingEvent = (key: string) => {
    mutateConfig((cfg) => {
      if (cfg.event) delete cfg.event[key];
    });
  };

  const renameMarketingEvent = (oldKey: string, newKey: string) => {
    const clean = newKey.trim().replace(/\s+/g, '_').toLowerCase();
    if (!clean || clean === oldKey) return;
    mutateConfig((cfg) => {
      if (!cfg.event?.[oldKey] || cfg.event[clean]) return;
      const rebuilt: Record<string, any> = {};
      for (const [k, v] of Object.entries<any>(cfg.event)) {
        if (k === oldKey) rebuilt[clean] = v;
        else rebuilt[k] = v;
      }
      cfg.event = rebuilt;
    });
  };

  const addGrowthYear = () => {
    mutateConfig((cfg) => {
      cfg.growth = cfg.growth || {};
      cfg.growth.yearly = cfg.growth.yearly || {};
      const years = Object.keys(cfg.growth.yearly)
        .map((k) => Number(k.replace('year_', '')))
        .filter((n) => !Number.isNaN(n));
      const next = (years.length ? Math.max(...years) : 0) + 1;
      cfg.growth.yearly[`year_${next}`] = {
        overall: { new_user: 1.0, visit: 1.0 },
        profile_multipliers: {
          conservative: { new_user: 1.0, visit: 1.0 },
          aggressive: { new_user: 1.0, visit: 1.0 },
          balanced: { new_user: 1.0, visit: 1.0 },
        },
      };
    });
  };

  const removeGrowthYear = (key: string) => {
    mutateConfig((cfg) => {
      if (cfg.growth?.yearly) delete cfg.growth.yearly[key];
    });
  };

  const addPeakHour = () => {
    mutateConfig((cfg) => {
      cfg.funnel = cfg.funnel || {};
      cfg.funnel.visit_hour_peak = cfg.funnel.visit_hour_peak || {};
      const ordinals = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth'];
      const next = ordinals.find((o) => !cfg.funnel.visit_hour_peak[o]) || `peak_${Date.now()}`;
      cfg.funnel.visit_hour_peak[next] = { weight: 5, hour: { min: 0, max: 23, avg: 12 } };
    });
  };

  const removePeakHour = (key: string) => {
    mutateConfig((cfg) => {
      if (cfg.funnel?.visit_hour_peak) delete cfg.funnel.visit_hour_peak[key];
    });
  };

  if (!parsedConfig) {
    return (
      <div className={`p-6 border ${theme.borderClass} ${theme.cardClass} text-center space-y-2`}>
        <div className="text-sm font-semibold text-rose-500">YAML Syntax Warning</div>
        <p className="text-xs opacity-70">
          The config contains syntax errors: {parseError}. Switch to the Raw YAML tab to inspect and fix.
        </p>
      </div>
    );
  }

  const startDateStr = parsedConfig.date?.start_date || '2026-01-01';
  const endDateStr = parsedConfig.date?.end_date || '2026-03-31';
  const timingTierKey = parsedConfig.tiers?.[selectedTimingTier]
    ? selectedTimingTier
    : Object.keys(parsedConfig.tiers || {})[0] || '';
  const timingTier = parsedConfig.tiers?.[timingTierKey] || {};

  const daysDiff = Math.max(
    1,
    Math.round((new Date(endDateStr).getTime() - new Date(startDateStr).getTime()) / (1000 * 3600 * 24)) + 1
  );

  return (
    <div className="space-y-6">
      {/* =========================================================================
          LEVEL 1: GENERAL QUICK CONTROLS (Always Visible)
      ========================================================================= */}
      <div className={`p-6 border ${theme.borderClass} ${theme.cardClass} space-y-6`}>
        <div className="flex items-center justify-between border-b pb-4 border-inherit">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider">General Simulation Controls</h2>
            </div>
            <p className={`text-xs ${theme.mutedClass} mt-0.5`}>
              High-level parameters for quick scenario adjustments.
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded font-mono font-bold opacity-80 border border-inherit">
            Horizon: {daysDiff} Days
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1: Horizon & Seed */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide">
              <Calendar className="w-3.5 h-3.5 opacity-70" />
              <span>Date Horizon</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={`text-[11px] block mb-1 ${theme.mutedClass}`}>Start Date</label>
                <input
                  type="date"
                  value={startDateStr}
                  onChange={(e) => updateField(['date', 'start_date'], e.target.value)}
                  className={`w-full rounded px-2.5 py-1.5 text-xs border ${theme.inputClass}`}
                />
              </div>
              <div>
                <label className={`text-[11px] block mb-1 ${theme.mutedClass}`}>End Date</label>
                <input
                  type="date"
                  value={endDateStr}
                  onChange={(e) => updateField(['date', 'end_date'], e.target.value)}
                  className={`w-full rounded px-2.5 py-1.5 text-xs border ${theme.inputClass}`}
                />
              </div>
            </div>

            {/* Quick Range Buttons */}
            <div className="flex items-center gap-1.5">
              {[7, 14, 30, 90, 180].map((d) => (
                <button
                  key={d}
                  onClick={() => setQuickDateRange(d)}
                  className={`flex-1 py-1 text-[11px] font-mono rounded border ${theme.buttonClass} transition ${
                    daysDiff === d ? 'ring-1 ring-emerald-500 font-bold' : ''
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>

            {/* Random Seed */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className={`text-[11px] ${theme.mutedClass}`}>Random Seed (Reproducibility)</label>
                <button
                  onClick={rollRandomSeed}
                  className="flex items-center gap-1 text-[10px] opacity-70 hover:opacity-100"
                >
                  <Dices className="w-3 h-3" /> Roll
                </button>
              </div>
              <input
                type="number"
                value={parsedConfig.simulation?.random_seed ?? 20260101}
                onChange={(e) => updateField(['simulation', 'random_seed'], Number(e.target.value))}
                className={`w-full rounded px-2.5 py-1.5 text-xs font-mono border ${theme.inputClass}`}
              />
            </div>
          </div>

          {/* Card 2: Basket Bounds with Paired Sliders + Number Inputs */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide">
              <ShoppingBag className="w-3.5 h-3.5 opacity-70" />
              <span>Basket Size Bounds</span>
            </div>

            {/* Min Items */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className={theme.mutedClass}>Min Items / Basket</span>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={parsedConfig.simulation?.basket?.min_items ?? 2}
                  onChange={(e) => updateField(['simulation', 'basket', 'min_items'], Number(e.target.value))}
                  className={`w-14 text-right rounded px-1.5 py-0.5 text-xs font-mono border ${theme.inputClass}`}
                />
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={parsedConfig.simulation?.basket?.min_items ?? 2}
                onChange={(e) => updateField(['simulation', 'basket', 'min_items'], Number(e.target.value))}
                className="w-full accent-slate-900 dark:accent-emerald-400 cursor-pointer"
              />
            </div>

            {/* Max Items */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className={theme.mutedClass}>Max Items / Basket</span>
                <input
                  type="number"
                  min="2"
                  max="30"
                  value={parsedConfig.simulation?.basket?.max_items ?? 8}
                  onChange={(e) => updateField(['simulation', 'basket', 'max_items'], Number(e.target.value))}
                  className={`w-14 text-right rounded px-1.5 py-0.5 text-xs font-mono border ${theme.inputClass}`}
                />
              </div>
              <input
                type="range"
                min="2"
                max="30"
                value={parsedConfig.simulation?.basket?.max_items ?? 8}
                onChange={(e) => updateField(['simulation', 'basket', 'max_items'], Number(e.target.value))}
                className="w-full accent-slate-900 dark:accent-emerald-400 cursor-pointer"
              />
            </div>

            {/* Price Variance */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className={theme.mutedClass}>Price Variation (Std Dev)</span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="0.25"
                  value={parsedConfig.simulation?.price_variation?.std_pct ?? 0.05}
                  onChange={(e) => updateField(['simulation', 'price_variation', 'std_pct'], parseFloat(e.target.value))}
                  className={`w-14 text-right rounded px-1.5 py-0.5 text-xs font-mono border ${theme.inputClass}`}
                />
              </div>
              <input
                type="range"
                min="0"
                max="0.25"
                step="0.01"
                value={parsedConfig.simulation?.price_variation?.std_pct ?? 0.05}
                onChange={(e) => updateField(['simulation', 'price_variation', 'std_pct'], parseFloat(e.target.value))}
                className="w-full accent-slate-900 dark:accent-emerald-400 cursor-pointer"
              />
            </div>
          </div>

          {/* Card 3: Key Conversion Rates with Paired Inputs */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide">
              <GitFork className="w-3.5 h-3.5 opacity-70" />
              <span>Key Funnel Rates</span>
            </div>

            {/* Product View Rate */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className={theme.mutedClass}>Landing &rarr; Product View</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.05"
                  max="1.0"
                  value={parsedConfig.funnel?.landing_page?.conversion_rate ?? 0.65}
                  onChange={(e) => updateField(['funnel', 'landing_page', 'conversion_rate'], parseFloat(e.target.value))}
                  className={`w-14 text-right rounded px-1.5 py-0.5 text-xs font-mono border ${theme.inputClass}`}
                />
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.01"
                value={parsedConfig.funnel?.landing_page?.conversion_rate ?? 0.65}
                onChange={(e) => updateField(['funnel', 'landing_page', 'conversion_rate'], parseFloat(e.target.value))}
                className="w-full accent-slate-900 dark:accent-emerald-400 cursor-pointer"
              />
            </div>

            {/* Cart &rarr; Checkout */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className={theme.mutedClass}>Cart &rarr; Checkout</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.05"
                  max="1.0"
                  value={parsedConfig.funnel?.add_to_cart?.conversion_rate ?? 0.6}
                  onChange={(e) => updateField(['funnel', 'add_to_cart', 'conversion_rate'], parseFloat(e.target.value))}
                  className={`w-14 text-right rounded px-1.5 py-0.5 text-xs font-mono border ${theme.inputClass}`}
                />
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.01"
                value={parsedConfig.funnel?.add_to_cart?.conversion_rate ?? 0.6}
                onChange={(e) => updateField(['funnel', 'add_to_cart', 'conversion_rate'], parseFloat(e.target.value))}
                className="w-full accent-slate-900 dark:accent-emerald-400 cursor-pointer"
              />
            </div>

            {/* Checkout &rarr; Paid */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className={theme.mutedClass}>Checkout &rarr; Paid</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.05"
                  max="1.0"
                  value={parsedConfig.funnel?.checkout?.conversion_rate ?? 0.7}
                  onChange={(e) => updateField(['funnel', 'checkout', 'conversion_rate'], parseFloat(e.target.value))}
                  className={`w-14 text-right rounded px-1.5 py-0.5 text-xs font-mono border ${theme.inputClass}`}
                />
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.01"
                value={parsedConfig.funnel?.checkout?.conversion_rate ?? 0.7}
                onChange={(e) => updateField(['funnel', 'checkout', 'conversion_rate'], parseFloat(e.target.value))}
                className="w-full accent-slate-900 dark:accent-emerald-400 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Toggle Button to Open Complete / Advanced Engine Controls */}
        <div className="pt-2 flex justify-center">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold border ${theme.buttonClass} transition`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>{showAdvanced ? 'Hide Complete Engine Parameters' : 'Show Complete Engine Parameters (Catalog, Events, Growth, Tiers)'}</span>
            {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* =========================================================================
          LEVEL 2: COMPLETE ENGINE CONTROLS (Progressive Disclosure)
      ========================================================================= */}
      {showAdvanced && (
        <div className={`p-6 border ${theme.borderClass} ${theme.cardClass} space-y-6 animate-in fade-in duration-200`}>
          {/* Sub-Navigation for Advanced Engine Tabs */}
          <div className="flex items-center justify-between border-b pb-3 border-inherit flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider">Comprehensive Engine Spec</h3>
            </div>

            <div className="flex items-center gap-1 bg-black/5 dark:bg-white/5 p-1 rounded border border-inherit text-xs flex-wrap">
              <button
                onClick={() => setActiveAdvancedTab('tiers')}
                className={`px-3 py-1 font-medium rounded transition ${
                  activeAdvancedTab === 'tiers' ? theme.accentClass : 'opacity-70 hover:opacity-100'
                }`}
              >
                Customer Tiers ({Object.keys(parsedConfig.tiers || {}).length})
              </button>
              <button
                onClick={() => setActiveAdvancedTab('catalog')}
                className={`px-3 py-1 font-medium rounded transition ${
                  activeAdvancedTab === 'catalog' ? theme.accentClass : 'opacity-70 hover:opacity-100'
                }`}
              >
                Catalog ({Object.keys(parsedConfig.catalog || {}).length} Categories)
              </button>
              <button
                onClick={() => setActiveAdvancedTab('funnel')}
                className={`px-3 py-1 font-medium rounded transition ${
                  activeAdvancedTab === 'funnel' ? theme.accentClass : 'opacity-70 hover:opacity-100'
                }`}
              >
                Stage Durations
              </button>
              <button
                onClick={() => setActiveAdvancedTab('events')}
                className={`px-3 py-1 font-medium rounded transition ${
                  activeAdvancedTab === 'events' ? theme.accentClass : 'opacity-70 hover:opacity-100'
                }`}
              >
                Marketing Events ({Object.keys(parsedConfig.event || {}).length})
              </button>
              <button
                onClick={() => setActiveAdvancedTab('growth')}
                className={`px-3 py-1 font-medium rounded transition ${
                  activeAdvancedTab === 'growth' ? theme.accentClass : 'opacity-70 hover:opacity-100'
                }`}
              >
                Growth Models
              </button>
            </div>
          </div>

          {/* Sub-Tab 1: Customer Tiers Deep Dive */}
          {activeAdvancedTab === 'tiers' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries<any>(parsedConfig.tiers || {}).map(([tierKey, tier]) => (
                <div key={tierKey} className="p-4 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-xs capitalize text-emerald-600 dark:text-emerald-400">
                        {tierKey.replace('_', ' ')}
                      </h4>
                      <p className={`text-[10px] ${theme.mutedClass}`}>{tier.description || tier.profile}</p>
                    </div>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded border border-inherit opacity-70">
                      {tier.profile}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Base Users</label>
                      <input
                        type="number"
                        min="0"
                        max="500"
                        value={tier.base_user ?? 10}
                        onChange={(e) => updateField(['tiers', tierKey, 'base_user'], Number(e.target.value))}
                        className={`w-full rounded px-2 py-1 text-xs font-mono border ${theme.inputClass}`}
                      />
                    </div>
                    <div>
                      <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Daily Arrival %</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={tier.daily_new_user_chance ?? 0.1}
                        onChange={(e) => updateField(['tiers', tierKey, 'daily_new_user_chance'], parseFloat(e.target.value))}
                        className={`w-full rounded px-2 py-1 text-xs font-mono border ${theme.inputClass}`}
                      />
                    </div>
                    <div>
                      <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Weekend Arrival %</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={tier.daily_new_user_chance_weekend ?? 0.15}
                        onChange={(e) => updateField(['tiers', tierKey, 'daily_new_user_chance_weekend'], parseFloat(e.target.value))}
                        className={`w-full rounded px-2 py-1 text-xs font-mono border ${theme.inputClass}`}
                      />
                    </div>
                  </div>

                  {/* Category Affinity Weights */}
                  {tier.category_weight && (
                    <div className="text-[11px] pt-2 border-t border-inherit/40 space-y-1.5">
                      <span className={`block font-semibold ${theme.mutedClass}`}>Category Weights</span>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-36 overflow-y-auto pr-1">
                        {Object.entries<number>(tier.category_weight).map(([cat, weight]) => (
                          <div key={cat} className="flex items-center justify-between text-[10px]">
                            <span className="truncate max-w-[80px] capitalize">{cat.replace('_', ' ')}</span>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              max="10"
                              value={weight}
                              onChange={(e) => updateField(['tiers', tierKey, 'category_weight', cat], parseFloat(e.target.value))}
                              className={`w-11 text-right rounded px-1 py-0.5 text-[10px] font-mono border ${theme.inputClass}`}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Sub-Tab 2: Catalog Categories (19 categories) */}
          {activeAdvancedTab === 'catalog' && (
            <div className="space-y-4 text-xs">
              <p className={theme.mutedClass}>
                All 19 product categories loaded directly from your product catalog with their repeat cooldown rules in days.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries<any>(parsedConfig.catalog || {}).map(([catKey, subcats]) => {
                  const totalProducts = Object.values<any>(subcats || {}).reduce(
                    (sum, s) => sum + Object.keys(s.product || {}).length,
                    0
                  );
                  return (
                    <div key={catKey} className="p-3.5 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                          {catKey.replace('_', ' ')}
                        </span>
                        <span className="text-[10px] opacity-70 font-mono">
                          {totalProducts} products
                        </span>
                      </div>
                      <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                        {Object.entries<any>(subcats || {}).map(([subcatKey, subcat]) => (
                          <div key={subcatKey} className="flex items-center justify-between text-[11px] py-0.5">
                            <span className="truncate capitalize">{subcatKey.replace('_', ' ')}</span>
                            <div className="flex items-center gap-1">
                              <span className={`text-[10px] ${theme.mutedClass}`}>Cooldown:</span>
                              <input
                                type="number"
                                min="0"
                                max="30"
                                value={subcat.cooldown ?? 1}
                                onChange={(e) => updateField(['catalog', catKey, subcatKey, 'cooldown'], Number(e.target.value))}
                                className={`w-10 text-right rounded px-1 py-0.5 text-[10px] font-mono border ${theme.inputClass}`}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Sub-Tab 3: Funnel Durations & Peak Hours */}
          {activeAdvancedTab === 'funnel' && (
            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <p className={`text-xs ${theme.mutedClass}`}>
                    Global stage timing defaults. Tier-specific values can override these settings below.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
                  {FUNNEL_STEPS.map((step) => {
                    const dur = parsedConfig.funnel?.[step]?.duration || {
                      min_duration: 5,
                      avg_duration: 180,
                      max_duration: 600,
                    };
                    return (
                      <div key={step} className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                        <span className="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">
                          {step.replace(/_/g, ' ')}
                        </span>
                        <div className="space-y-1.5">
                          <div className="flex justify-between items-center">
                            <span className={theme.mutedClass}>Min Secs:</span>
                            <input
                              type="number"
                              min="0"
                              value={dur.min_duration}
                              onChange={(e) => updateField(['funnel', step, 'duration', 'min_duration'], Number(e.target.value))}
                              className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div className="flex justify-between items-center">
                            <span className={theme.mutedClass}>Avg Secs:</span>
                            <input
                              type="number"
                              min="0"
                              value={dur.avg_duration}
                              onChange={(e) => updateField(['funnel', step, 'duration', 'avg_duration'], Number(e.target.value))}
                              className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div className="flex justify-between items-center">
                            <span className={theme.mutedClass}>Max Secs:</span>
                            <input
                              type="number"
                              min="0"
                              value={dur.max_duration}
                              onChange={(e) => updateField(['funnel', step, 'duration', 'max_duration'], Number(e.target.value))}
                              className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Tier-specific timing overrides */}
              {Object.keys(parsedConfig.tiers || {}).length > 0 && (
                <div className="space-y-3 pt-4 border-t border-inherit">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h4 className="text-xs font-bold uppercase tracking-wider">Tier Timing Overrides</h4>
                    <select
                      value={timingTierKey}
                      onChange={(e) => setSelectedTimingTier(e.target.value)}
                      className={`rounded px-2 py-1 text-xs border ${theme.inputClass}`}
                    >
                      {Object.keys(parsedConfig.tiers).map((tierKey) => (
                        <option key={tierKey} value={tierKey}>
                          {tierKey}
                        </option>
                      ))}
                    </select>
                    <span className={`text-[11px] ${theme.mutedClass}`}>
                      Edit the selected tier's stage duration and peak-hour settings.
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
                    {FUNNEL_STEPS.map((step) => {
                      const duration = {
                        ...(parsedConfig.funnel?.[step]?.duration || {}),
                        ...(timingTier[step]?.duration || {}),
                      };
                      return (
                        <div key={step} className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                          <span className="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">
                            {step.replace(/_/g, ' ')}
                          </span>
                          {(['min_duration', 'avg_duration', 'max_duration'] as const).map((field) => (
                            <div key={field} className="flex justify-between items-center gap-1">
                              <span className={theme.mutedClass}>
                                {field === 'min_duration' ? 'Min' : field === 'avg_duration' ? 'Avg' : 'Max'} Secs:
                              </span>
                              <input
                                type="number"
                                min="0"
                                value={duration[field] ?? 0}
                                onChange={(e) =>
                                  updateField(
                                    ['tiers', timingTierKey, step, 'duration', field],
                                    Number(e.target.value)
                                  )
                                }
                                className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                              />
                            </div>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                  <div className="space-y-2">
                    <span className={`block text-[11px] font-semibold uppercase ${theme.mutedClass}`}>
                      {timingTierKey} Peak Visit Hours
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                      {Object.entries<any>({
                        ...(parsedConfig.funnel?.visit_hour_peak || {}),
                        ...(timingTier.visit_hour_peak || {}),
                      }).map(([peakKey, peak]) => (
                        <div key={peakKey} className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5">
                          <span className="font-bold uppercase text-emerald-600 dark:text-emerald-400">
                            {peakKey}
                          </span>
                          <div className="grid grid-cols-2 gap-2 mt-2">
                            {(['weight', 'avg', 'min', 'max'] as const).map((field) => {
                              const value = field === 'weight' ? peak.weight : peak.hour?.[field];
                              return (
                                <label key={field} className={`flex items-center justify-between gap-2 ${theme.mutedClass}`}>
                                  <span>{field === 'avg' ? 'Avg hour' : field === 'min' ? 'Min hour' : field === 'max' ? 'Max hour' : 'Weight'}</span>
                                  <input
                                    type="number"
                                    min="0"
                                    max={field === 'weight' ? undefined : 23}
                                    value={value ?? (field === 'weight' ? 1 : field === 'avg' ? 12 : field === 'min' ? 0 : 23)}
                                    onChange={(e) =>
                                      updateField(
                                        field === 'weight'
                                          ? ['tiers', timingTierKey, 'visit_hour_peak', peakKey, 'weight']
                                          : ['tiers', timingTierKey, 'visit_hour_peak', peakKey, 'hour', field],
                                        Number(e.target.value)
                                      )
                                    }
                                    className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                                  />
                                </label>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                      {Object.keys({
                        ...(parsedConfig.funnel?.visit_hour_peak || {}),
                        ...(timingTier.visit_hour_peak || {}),
                      }).length === 0 && (
                        <p className={`text-[11px] ${theme.mutedClass}`}>No peak hours configured for this tier or globally.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Peak visit hours */}
              <div className="space-y-3 pt-4 border-t border-inherit">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider">Peak Visit Hours</h4>
                      <p className={`text-[11px] ${theme.mutedClass}`}>
                        Weighted daily traffic peaks. Higher weight = more sessions land in that window.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={addPeakHour}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold border ${theme.buttonClass}`}
                  >
                    <Plus className="w-3 h-3" /> Add Peak
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                  {Object.entries<any>(parsedConfig.funnel?.visit_hour_peak || {}).map(([peakKey, peak]) => {
                    const hour = peak?.hour || { min: 0, max: 23, avg: 12 };
                    return (
                      <div key={peakKey} className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                            {peakKey}
                          </span>
                          <button
                            onClick={() => removePeakHour(peakKey)}
                            className="opacity-60 hover:opacity-100 hover:text-rose-500"
                            title="Remove peak"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Weight</label>
                            <input
                              type="number"
                              min="0"
                              step="1"
                              value={peak.weight ?? 1}
                              onChange={(e) => updateField(['funnel', 'visit_hour_peak', peakKey, 'weight'], Number(e.target.value))}
                              className={`w-full rounded px-2 py-1 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div>
                            <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Avg Hour</label>
                            <input
                              type="number"
                              min="0"
                              max="23"
                              value={hour.avg ?? 12}
                              onChange={(e) => updateField(['funnel', 'visit_hour_peak', peakKey, 'hour', 'avg'], Number(e.target.value))}
                              className={`w-full rounded px-2 py-1 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div>
                            <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Min Hour</label>
                            <input
                              type="number"
                              min="0"
                              max="23"
                              value={hour.min ?? 0}
                              onChange={(e) => updateField(['funnel', 'visit_hour_peak', peakKey, 'hour', 'min'], Number(e.target.value))}
                              className={`w-full rounded px-2 py-1 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div>
                            <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Max Hour</label>
                            <input
                              type="number"
                              min="0"
                              max="23"
                              value={hour.max ?? 23}
                              onChange={(e) => updateField(['funnel', 'visit_hour_peak', peakKey, 'hour', 'max'], Number(e.target.value))}
                              className={`w-full rounded px-2 py-1 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {Object.keys(parsedConfig.funnel?.visit_hour_peak || {}).length === 0 && (
                    <p className={`text-[11px] ${theme.mutedClass}`}>
                      No peaks configured — visits fall back to a 19:00 average.
                    </p>
                  )}
                </div>
              </div>

              {/* Funnel noise */}
              <div className="pt-4 border-t border-inherit grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                  <span className="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">
                    Funnel Noise
                  </span>
                  <div className="flex justify-between items-center">
                    <span className={theme.mutedClass}>Multiplier:</span>
                    <input
                      type="number"
                      step="0.01"
                      min="1"
                      value={parsedConfig.funnel?.funnel_noise?.multiplier ?? 1.15}
                      onChange={(e) => updateField(['funnel', 'funnel_noise', 'multiplier'], parseFloat(e.target.value))}
                      className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className={theme.mutedClass}>Distribution:</span>
                    <select
                      value={parsedConfig.funnel?.funnel_noise?.distribution ?? 'lognormal'}
                      onChange={(e) => updateField(['funnel', 'funnel_noise', 'distribution'], e.target.value)}
                      className={`rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                    >
                      {['lognormal', 'normal', 'poisson', 'uniform'].map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                  <span className="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">
                    Reactivation
                  </span>
                  <div className="flex justify-between items-center">
                    <span className={theme.mutedClass}>Lapsed Return Chance:</span>
                    <input
                      type="number"
                      step="0.001"
                      min="0"
                      max="1"
                      value={parsedConfig.simulation?.reactivation_probability ?? 0.002}
                      onChange={(e) =>
                        updateField(['simulation', 'reactivation_probability'], parseFloat(e.target.value))
                      }
                      className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                    />
                  </div>
                  <p className={`text-[10px] ${theme.mutedClass}`}>
                    Daily chance a fully decayed customer returns.
                  </p>
                </div>
              </div>

              {/* Visit decay curve */}
              <div className="pt-4 border-t border-inherit space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider">Visit Decay Curve</h4>
                    <p className={`text-[11px] ${theme.mutedClass}`}>
                      Engagement multiplier by days since the customer's last visit.
                    </p>
                  </div>
                  <button
                    onClick={() =>
                      mutateConfig((cfg) => {
                        cfg.simulation = cfg.simulation || {};
                        const decay = Array.isArray(cfg.simulation.visit_decay) ? cfg.simulation.visit_decay : [];
                        const lastDays = decay.length ? Number(decay[decay.length - 1].days) : 0;
                        decay.push({ days: lastDays + 30, multiplier: 0.0 });
                        cfg.simulation.visit_decay = decay;
                      })
                    }
                    className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold border ${theme.buttonClass}`}
                  >
                    <Plus className="w-3 h-3" /> Add Rule
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 text-xs">
                  {(parsedConfig.simulation?.visit_decay || []).map((rule: any, idx: number) => (
                    <div key={idx} className="p-2 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] ${theme.mutedClass}`}>Day {rule.days}</span>
                        <button
                          onClick={() =>
                            mutateConfig((cfg) => {
                              cfg.simulation.visit_decay.splice(idx, 1);
                            })
                          }
                          className="opacity-60 hover:opacity-100 hover:text-rose-500"
                          title="Remove rule"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                      <input
                        type="number"
                        min="0"
                        value={rule.days}
                        onChange={(e) => updateField(['simulation', 'visit_decay', String(idx), 'days'], Number(e.target.value))}
                        className={`w-full rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                      />
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={rule.multiplier}
                        onChange={(e) =>
                          updateField(['simulation', 'visit_decay', String(idx), 'multiplier'], parseFloat(e.target.value))
                        }
                        className={`w-full rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Sub-Tab 4: Marketing Events & Campaigns */}
          {activeAdvancedTab === 'events' && (
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <Megaphone className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <p className={theme.mutedClass}>
                    Marketing campaigns and promotional calendar multipliers configured in <code>config/event.yaml</code>.
                  </p>
                </div>
                <button
                  onClick={addMarketingEvent}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold border ${theme.buttonClass}`}
                >
                  <Plus className="w-3 h-3" /> Add Campaign
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries<any>(parsedConfig.event || {}).map(([evtKey, evt]) => (
                  <div key={evtKey} className="p-3.5 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <input
                        value={evt.name ?? evtKey}
                        onChange={(e) => updateField(['event', evtKey, 'name'], e.target.value)}
                        className={`flex-1 min-w-0 rounded px-2 py-1 text-xs font-bold border ${theme.inputClass}`}
                      />
                      <button
                        onClick={() => removeMarketingEvent(evtKey)}
                        className="opacity-60 hover:opacity-100 hover:text-rose-500 shrink-0"
                        title="Remove campaign"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div>
                      <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Campaign Key</label>
                      <input
                        defaultValue={evtKey}
                        onBlur={(e) => renameMarketingEvent(evtKey, e.target.value)}
                        className={`w-full rounded px-2 py-1 text-[11px] font-mono border ${theme.inputClass}`}
                      />
                    </div>

                    <div>
                      <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Description</label>
                      <input
                        value={evt.description ?? ''}
                        onChange={(e) => updateField(['event', evtKey, 'description'], e.target.value)}
                        className={`w-full rounded px-2 py-1 text-[11px] border ${theme.inputClass}`}
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Year</label>
                        <input
                          type="number"
                          min="1"
                          value={evt.year ?? 1}
                          onChange={(e) => updateField(['event', evtKey, 'year'], Number(e.target.value))}
                          className={`w-full rounded px-2 py-1 font-mono border ${theme.inputClass}`}
                        />
                      </div>
                      <div>
                        <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>Start Month</label>
                        <select
                          value={evt.start_month ?? 1}
                          onChange={(e) => updateField(['event', evtKey, 'start_month'], Number(e.target.value))}
                          className={`w-full rounded px-1 py-1 font-mono border ${theme.inputClass}`}
                        >
                          {MONTHS.map((m, i) => (
                            <option key={m} value={i + 1}>
                              {m.slice(0, 3)}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className={`text-[10px] block mb-0.5 ${theme.mutedClass}`}>End Month</label>
                        <select
                          value={evt.end_month ?? 12}
                          onChange={(e) => updateField(['event', evtKey, 'end_month'], Number(e.target.value))}
                          className={`w-full rounded px-1 py-1 font-mono border ${theme.inputClass}`}
                        >
                          {MONTHS.map((m, i) => (
                            <option key={m} value={i + 1}>
                              {m.slice(0, 3)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-inherit/40 space-y-1.5">
                      <span className={`block text-[10px] font-semibold uppercase ${theme.mutedClass}`}>
                        Overall Multipliers
                      </span>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[10px]">Visit</span>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={evt.overall?.visit ?? 1}
                            onChange={(e) => updateField(['event', evtKey, 'overall', 'visit'], parseFloat(e.target.value))}
                            className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                          />
                        </div>
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[10px]">New User</span>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={evt.overall?.new_user ?? 1}
                            onChange={(e) => updateField(['event', evtKey, 'overall', 'new_user'], parseFloat(e.target.value))}
                            className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                          />
                        </div>
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[10px]">Conversion</span>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={evt.overall?.conversion ?? 1}
                            onChange={(e) =>
                              updateField(['event', evtKey, 'overall', 'conversion'], parseFloat(e.target.value))
                            }
                            className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Profile targeting */}
                    <div className="pt-2 border-t border-inherit/40 space-y-1.5">
                      <span className={`block text-[10px] font-semibold uppercase ${theme.mutedClass}`}>
                        Profile Targeting
                      </span>
                      {['conservative', 'balanced', 'aggressive'].map((prof) => {
                        const profCfg = evt.profiles?.[prof];
                        return (
                          <div key={prof} className="rounded border border-inherit/50 p-2 space-y-1">
                            <span className="text-[10px] capitalize font-semibold">{prof}</span>
                            <div className="grid grid-cols-2 gap-2">
                              {(['visit', 'new_user'] as const).map((metric) => (
                                <label key={metric} className="flex items-center justify-between gap-1 text-[10px]">
                                  <span>{metric === 'new_user' ? 'New user' : 'Visit'}</span>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    placeholder="—"
                                    value={profCfg?.[metric] ?? ''}
                                    onChange={(e) => {
                                      const val = e.target.value === '' ? undefined : parseFloat(e.target.value);
                                      mutateConfig((cfg) => {
                                        const target = cfg.event?.[evtKey];
                                        if (!target) return;
                                        if (val === undefined) {
                                          if (target.profiles?.[prof]) {
                                            delete target.profiles[prof][metric];
                                            if (Object.keys(target.profiles[prof]).length === 0) delete target.profiles[prof];
                                            if (Object.keys(target.profiles).length === 0) delete target.profiles;
                                          }
                                        } else {
                                          target.profiles = target.profiles || {};
                                          target.profiles[prof] = target.profiles[prof] || {};
                                          target.profiles[prof][metric] = val;
                                        }
                                      });
                                    }}
                                    className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                                  />
                                </label>
                              ))}
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              {FUNNEL_STEPS.slice(0, -1).map((step) => (
                                <label key={step} className="flex items-center justify-between gap-1 text-[10px]">
                                  <span className="truncate">{step.replace(/_/g, ' ')}</span>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    placeholder="—"
                                    value={profCfg?.conversion?.[step] ?? ''}
                                    onChange={(e) => {
                                      const val = e.target.value === '' ? undefined : parseFloat(e.target.value);
                                      mutateConfig((cfg) => {
                                        const target = cfg.event?.[evtKey];
                                        if (!target) return;
                                        if (val === undefined) {
                                          if (target.profiles?.[prof]?.conversion) {
                                            delete target.profiles[prof].conversion[step];
                                            if (Object.keys(target.profiles[prof].conversion).length === 0) {
                                              delete target.profiles[prof].conversion;
                                            }
                                            if (Object.keys(target.profiles[prof]).length === 0) delete target.profiles[prof];
                                            if (Object.keys(target.profiles).length === 0) delete target.profiles;
                                          }
                                        } else {
                                          target.profiles = target.profiles || {};
                                          target.profiles[prof] = target.profiles[prof] || {};
                                          target.profiles[prof].conversion = target.profiles[prof].conversion || {};
                                          target.profiles[prof].conversion[step] = val;
                                        }
                                      });
                                    }}
                                    className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                                  />
                                </label>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
                {Object.keys(parsedConfig.event || {}).length === 0 && (
                  <p className={`text-[11px] ${theme.mutedClass}`}>
                    No campaigns yet. Add one to model seasonal traffic spikes.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Sub-Tab 5: Growth Models */}
          {activeAdvancedTab === 'growth' && (
            <div className="space-y-5 text-xs">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <p className={theme.mutedClass}>
                  Macro growth profiles and yearly lifecycle multipliers configured in <code>config/growth.yaml</code>.
                </p>
              </div>

              {/* Base overall multipliers */}
              <div className="p-3.5 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                <h4 className="text-[11px] font-bold uppercase tracking-wider">Base Overall Multipliers</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {(['new_user', 'visit', 'conversion'] as const).map((metric) => (
                    <label key={metric} className="flex items-center justify-between gap-2">
                      <span className={`text-[11px] capitalize ${theme.mutedClass}`}>
                        {metric.replace('_', ' ')}
                      </span>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={parsedConfig.growth?.base?.overall?.[metric] ?? 1}
                        onChange={(e) =>
                          updateField(['growth', 'base', 'overall', metric], parseFloat(e.target.value))
                        }
                        className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                      />
                    </label>
                  ))}
                </div>
              </div>

              {/* Base tier profiles */}
              <div className="space-y-2">
                <h4 className="text-[11px] font-bold uppercase tracking-wider">Base Tier Profiles</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {['conservative', 'balanced', 'aggressive'].map((prof) => {
                    const pData = parsedConfig.growth?.base?.tier_profiles?.[prof] || {};
                    return (
                      <div key={prof} className="p-3.5 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                        <span className="font-bold text-xs capitalize text-emerald-600 dark:text-emerald-400">{prof}</span>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between gap-1">
                            <span className={`text-[11px] ${theme.mutedClass}`}>New User Growth</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={pData.new_user ?? 1.0}
                              onChange={(e) =>
                                updateField(['growth', 'base', 'tier_profiles', prof, 'new_user'], parseFloat(e.target.value))
                              }
                              className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div className="flex items-center justify-between gap-1">
                            <span className={`text-[11px] ${theme.mutedClass}`}>Visit Engagement</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={pData.visit ?? 1.0}
                              onChange={(e) =>
                                updateField(['growth', 'base', 'tier_profiles', prof, 'visit'], parseFloat(e.target.value))
                              }
                              className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div className="flex items-center justify-between gap-1">
                            <span className={`text-[11px] ${theme.mutedClass}`}>Conversion</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={pData.conversion ?? 1.0}
                              onChange={(e) =>
                                updateField(
                                  ['growth', 'base', 'tier_profiles', prof, 'conversion'],
                                  parseFloat(e.target.value)
                                )
                              }
                              className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Yearly lifecycle stages */}
              <div className="space-y-2 pt-3 border-t border-inherit">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <h4 className="text-[11px] font-bold uppercase tracking-wider">Yearly Lifecycle Stages</h4>
                    <p className={`text-[11px] ${theme.mutedClass}`}>
                      Multipliers applied per simulation year. <code>year_8_plus</code> is the long-term fallback.
                    </p>
                  </div>
                  <button
                    onClick={addGrowthYear}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold border ${theme.buttonClass}`}
                  >
                    <Plus className="w-3 h-3" /> Add Year
                  </button>
                </div>

                <div className="space-y-2">
                  {Object.entries<any>(parsedConfig.growth?.yearly || {}).map(([yearKey, yearCfg]) => (
                    <div key={yearKey} className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                          {yearKey.replace(/_/g, ' ')}
                        </span>
                        <button
                          onClick={() => removeGrowthYear(yearKey)}
                          className="opacity-60 hover:opacity-100 hover:text-rose-500"
                          title="Remove year stage"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        {/* Overall */}
                        <div className="space-y-1.5">
                          <span className={`block text-[10px] font-semibold uppercase ${theme.mutedClass}`}>Overall</span>
                          <div className="flex items-center justify-between gap-1">
                            <span className="text-[10px]">New User</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={yearCfg.overall?.new_user ?? 1}
                              onChange={(e) =>
                                updateField(['growth', 'yearly', yearKey, 'overall', 'new_user'], parseFloat(e.target.value))
                              }
                              className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div className="flex items-center justify-between gap-1">
                            <span className="text-[10px]">Visit</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={yearCfg.overall?.visit ?? 1}
                              onChange={(e) =>
                                updateField(['growth', 'yearly', yearKey, 'overall', 'visit'], parseFloat(e.target.value))
                              }
                              className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                          <div className="flex items-center justify-between gap-1">
                            <span className="text-[10px]">Conversion</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={yearCfg.overall?.conversion ?? 1}
                              onChange={(e) =>
                                updateField(
                                  ['growth', 'yearly', yearKey, 'overall', 'conversion'],
                                  parseFloat(e.target.value)
                                )
                              }
                              className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                            />
                          </div>
                        </div>

                        {/* Per-profile multipliers */}
                        {['conservative', 'balanced', 'aggressive'].map((prof) => {
                          const profCfg = yearCfg.profile_multipliers?.[prof] || {};
                          return (
                            <div key={prof} className="space-y-1.5">
                              <span className={`block text-[10px] font-semibold uppercase ${theme.mutedClass}`}>
                                {prof}
                              </span>
                              <div className="flex items-center justify-between gap-1">
                                <span className="text-[10px]">New User</span>
                                <input
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  value={profCfg.new_user ?? 1}
                                  onChange={(e) =>
                                    updateField(
                                      ['growth', 'yearly', yearKey, 'profile_multipliers', prof, 'new_user'],
                                      parseFloat(e.target.value)
                                    )
                                  }
                                  className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                                />
                              </div>
                              <div className="flex items-center justify-between gap-1">
                                <span className="text-[10px]">Visit</span>
                                <input
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  value={profCfg.visit ?? 1}
                                  onChange={(e) =>
                                    updateField(
                                      ['growth', 'yearly', yearKey, 'profile_multipliers', prof, 'visit'],
                                      parseFloat(e.target.value)
                                    )
                                  }
                                  className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                                />
                              </div>
                              <div className="flex items-center justify-between gap-1">
                                <span className="text-[10px]">Conversion</span>
                                <input
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  value={profCfg.conversion ?? 1}
                                  onChange={(e) =>
                                    updateField(
                                      ['growth', 'yearly', yearKey, 'profile_multipliers', prof, 'conversion'],
                                      parseFloat(e.target.value)
                                    )
                                  }
                                  className={`w-14 text-right rounded px-1 py-0.5 font-mono border ${theme.inputClass}`}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                  {Object.keys(parsedConfig.growth?.yearly || {}).length === 0 && (
                    <p className={`text-[11px] ${theme.mutedClass}`}>
                      No yearly stages — growth multipliers stay at 1.0x.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
