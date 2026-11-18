import React from 'react';
import { Play, Download, Sparkles, Sliders, BarChart3, Code, Sun, Moon } from 'lucide-react';
import { PRESET_SCENARIOS } from '../presets';
import { ThemeConfig } from '../types/theme';

interface HeaderProps {
  currentPresetId: string;
  onSelectPreset: (id: string) => void;
  isRunning: boolean;
  onRunSimulation: () => void;
  onOpenExport: () => void;
  hasOutput: boolean;
  activeTab: 'studio' | 'dashboard' | 'yaml';
  onChangeTab: (tab: 'studio' | 'dashboard' | 'yaml') => void;
  theme: ThemeConfig;
  onToggleThemeMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentPresetId,
  onSelectPreset,
  isRunning,
  onRunSimulation,
  onOpenExport,
  hasOutput,
  activeTab,
  onChangeTab,
  theme,
  onToggleThemeMode,
}) => {
  return (
    <header className={`border-b ${theme.headerClass} sticky top-0 z-30 px-6 py-3 transition-colors duration-150`}>
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand & Tabs */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2.5">
            <div className="h-8 w-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white text-base shadow-sm">
              🥬
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-tight">Creanu Labs</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded border border-inherit opacity-70">
                  Swiss Design
                </span>
              </div>
            </div>
          </div>

          {/* Primary View Tabs */}
          <nav className="flex items-center gap-1 p-1 rounded-lg border border-inherit bg-black/5 dark:bg-white/5">
            <button
              onClick={() => onChangeTab('studio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                activeTab === 'studio' ? theme.accentClass : 'opacity-70 hover:opacity-100'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Config Studio</span>
            </button>

            <button
              onClick={() => onChangeTab('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                activeTab === 'dashboard' ? theme.accentClass : 'opacity-70 hover:opacity-100'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Analytics Dashboard</span>
            </button>

            <button
              onClick={() => onChangeTab('yaml')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                activeTab === 'yaml' ? theme.accentClass : 'opacity-70 hover:opacity-100'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Raw YAML</span>
            </button>
          </nav>
        </div>

        {/* Right Side: Preset, Light/Dark Toggle, Actions */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Light / Dark Mode Toggle */}
          <button
            onClick={onToggleThemeMode}
            className={`p-2 rounded-md border transition ${theme.buttonClass}`}
            title={`Switch to ${theme.mode === 'light' ? 'Dark' : 'Light'} Mode`}
          >
            {theme.mode === 'light' ? (
              <Moon className="w-4 h-4 text-slate-700" />
            ) : (
              <Sun className="w-4 h-4 text-amber-400" />
            )}
          </button>

          {/* Grocery Preset Dropdown */}
          <div className="flex items-center gap-1.5 p-1 rounded-md border border-inherit text-xs bg-black/5 dark:bg-white/5">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600 ml-1" />
            <select
              value={currentPresetId}
              onChange={(e) => onSelectPreset(e.target.value)}
              className="bg-transparent text-xs font-medium focus:outline-none cursor-pointer pr-1"
            >
              {PRESET_SCENARIOS.map((p) => (
                <option key={p.id} value={p.id} className={theme.mode === 'dark' ? 'bg-[#15181e] text-white' : 'bg-white text-slate-900'}>
                  {p.title}
                </option>
              ))}
            </select>
          </div>

          {/* Run Button */}
          <button
            onClick={onRunSimulation}
            disabled={isRunning}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-bold transition active:scale-95 disabled:opacity-50 ${theme.accentClass}`}
          >
            {isRunning ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run</span>
              </>
            )}
          </button>

          {/* Export Button */}
          <button
            onClick={onOpenExport}
            disabled={!hasOutput}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold border transition disabled:opacity-40 ${theme.buttonClass}`}
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download ZIP</span>
          </button>
        </div>
      </div>
    </header>
  );
};
