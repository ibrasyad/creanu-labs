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
} from 'lucide-react';
import { ThemeConfig } from '../types/theme';

interface ConfigEditorProps {
  yamlContent: string;
  onChangeYaml: (val: string) => void;
  theme: ThemeConfig;
}

export const ConfigEditor: React.FC<ConfigEditorProps> = ({
  yamlContent,
  onChangeYaml,
  theme,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeAdvancedTab, setActiveAdvancedTab] = useState<'tiers' | 'catalog' | 'funnel' | 'events' | 'growth'>('tiers');

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

          {/* Sub-Tab 3: Funnel Durations */}
          {activeAdvancedTab === 'funnel' && (
            <div className="space-y-3">
              <p className={`text-xs ${theme.mutedClass}`}>
                Configure average session dwell time (in seconds) spent by shoppers at each step before advancing or dropping off.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                {['landing_page', 'product_view', 'add_to_cart', 'checkout'].map((step) => {
                  const dur = parsedConfig.funnel?.[step]?.duration || { min_duration: 5, avg_duration: 180, max_duration: 600 };
                  return (
                    <div key={step} className="p-3 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                      <span className="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">
                        {step.replace('_', ' ')}
                      </span>
                      <div className="space-y-1.5">
                        <div className="flex justify-between items-center">
                          <span className={theme.mutedClass}>Min Secs:</span>
                          <input
                            type="number"
                            min="1"
                            value={dur.min_duration}
                            onChange={(e) => updateField(['funnel', step, 'duration', 'min_duration'], Number(e.target.value))}
                            className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                          />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className={theme.mutedClass}>Avg Secs:</span>
                          <input
                            type="number"
                            min="5"
                            value={dur.avg_duration}
                            onChange={(e) => updateField(['funnel', step, 'duration', 'avg_duration'], Number(e.target.value))}
                            className={`w-16 text-right rounded px-1.5 py-0.5 font-mono border ${theme.inputClass}`}
                          />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className={theme.mutedClass}>Max Secs:</span>
                          <input
                            type="number"
                            min="10"
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
          )}

          {/* Sub-Tab 4: Marketing Events & Campaigns */}
          {activeAdvancedTab === 'events' && (
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2">
                <Megaphone className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <p className={theme.mutedClass}>
                  Marketing campaigns and promotional calendar multipliers configured in <code>config/event.yaml</code>.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries<any>(parsedConfig.event || {}).map(([evtKey, evt]) => (
                  <div key={evtKey} className="p-3.5 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs uppercase text-emerald-600 dark:text-emerald-400">
                        {evt.name || evtKey}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-inherit opacity-70">
                        Year {evt.year} &bull; M{evt.start_month || 1}-{evt.end_month || 12}
                      </span>
                    </div>
                    <p className={`text-[10px] ${theme.mutedClass}`}>{evt.description || 'Promotional traffic spike'}</p>
                    {evt.overall && (
                      <div className="pt-2 border-t border-inherit/40 grid grid-cols-2 gap-2 text-[10px] font-mono">
                        {evt.overall.visit && <div>Visit Boost: <strong>{evt.overall.visit}x</strong></div>}
                        {evt.overall.new_user && <div>Acquisition: <strong>{evt.overall.new_user}x</strong></div>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sub-Tab 5: Growth Models */}
          {activeAdvancedTab === 'growth' && (
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <p className={theme.mutedClass}>
                  Macro growth profiles and yearly lifecycle multipliers configured in <code>config/growth.yaml</code>.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {['conservative', 'balanced', 'aggressive'].map((prof) => {
                  const pData = parsedConfig.growth?.base?.tier_profiles?.[prof] || {};
                  return (
                    <div key={prof} className="p-3.5 rounded border border-inherit bg-black/5 dark:bg-white/5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs capitalize text-emerald-600 dark:text-emerald-400">{prof}</span>
                        <span className="text-[10px] opacity-70 font-mono">Profile</span>
                      </div>
                      <div className="space-y-1 text-[11px] font-mono">
                        <div className="flex justify-between">
                          <span className={theme.mutedClass}>New User Growth:</span>
                          <span>{pData.new_user ?? 1.0}x</span>
                        </div>
                        <div className="flex justify-between">
                          <span className={theme.mutedClass}>Visit Engagement:</span>
                          <span>{pData.visit ?? 1.0}x</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
