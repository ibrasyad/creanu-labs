import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ConfigEditor } from './components/ConfigEditor';
import { RawYamlEditor } from './components/RawYamlEditor';
import { SummaryDashboard } from './components/SummaryDashboard';
import { ExportModal } from './components/ExportModal';
import { ProgressBar } from './components/ProgressBar';
import { PRESET_SCENARIOS } from './presets';
import { DEFAULT_CONFIG_YAML } from './engine/defaultConfig';
import { runSimulationClient } from './engine/simulator';
import { SimulationOutput } from './types/simulation';
import { ThemeMode, SWISS_THEMES } from './types/theme';
import { Sparkles, BarChart2 } from 'lucide-react';
import yaml from 'js-yaml';

export function App() {
  const [themeMode, setThemeMode] = useState<ThemeMode>('light');
  const [activeTab, setActiveTab] = useState<'studio' | 'dashboard' | 'yaml'>('studio');

  const [currentPresetId, setCurrentPresetId] = useState<string>('default');
  const [configYaml, setConfigYaml] = useState<string>(DEFAULT_CONFIG_YAML);

  const [output, setOutput] = useState<SimulationOutput | null>(null);
  const [baselineOutput, setBaselineOutput] = useState<SimulationOutput | null>(null);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [progress, setProgress] = useState<{ day: number; total: number; dateStr: string } | null>(null);
  const [isExportOpen, setIsExportOpen] = useState<boolean>(false);

  const theme = SWISS_THEMES[themeMode];

  // Run a 90-day steady-state baseline simulation on mount for accurate statistical averages
  useEffect(() => {
    try {
      // Create a 90-day baseline config (2026-01-01 to 2026-03-31)
      const baselineCfgObj = yaml.load(DEFAULT_CONFIG_YAML) as any;
      if (baselineCfgObj.date) {
        baselineCfgObj.date.start_date = '2026-01-01';
        baselineCfgObj.date.end_date = '2026-03-31';
      }
      const baselineYaml90d = yaml.dump(baselineCfgObj);
      const baseline90d = runSimulationClient(baselineYaml90d);
      setBaselineOutput(baseline90d);

      // Run initial 14-day default output for the user's initial screen
      const initial14d = runSimulationClient(DEFAULT_CONFIG_YAML);
      setOutput(initial14d);
    } catch (err) {
      console.error('Initial baseline simulation error:', err);
    }
  }, []);

  // Preset Selection
  const handleSelectPreset = (presetId: string) => {
    setCurrentPresetId(presetId);
    const chosen = PRESET_SCENARIOS.find((p) => p.id === presetId);
    if (chosen) {
      setConfigYaml(chosen.configYaml);
    }
  };

  // Run Simulation Handler
  const handleRunSimulation = () => {
    setIsRunning(true);
    setProgress({ day: 0, total: 14, dateStr: 'Initializing...' });

    setTimeout(() => {
      try {
        const result = runSimulationClient(configYaml, (day, totalDays, dateStr) => {
          setProgress({ day, total: totalDays, dateStr });
        });
        setOutput(result);
        // Switch to dashboard view to immediately showcase results
        setActiveTab('dashboard');
      } catch (err: any) {
        alert(`Simulation error: ${err.message}`);
      } finally {
        setIsRunning(false);
        setProgress(null);
      }
    }, 40);
  };

  return (
    <div className={`min-h-screen flex flex-col ${theme.bodyClass} transition-colors duration-150`}>
      {/* Top Header */}
      <Header
        currentPresetId={currentPresetId}
        onSelectPreset={handleSelectPreset}
        isRunning={isRunning}
        onRunSimulation={handleRunSimulation}
        onOpenExport={() => setIsExportOpen(true)}
        hasOutput={output !== null}
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        theme={theme}
        onToggleThemeMode={() => setThemeMode((m) => (m === 'light' ? 'dark' : 'light'))}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Progress Bar (during active simulation) */}
        {isRunning && progress && (
          <ProgressBar
            currentDay={progress.day}
            totalDays={progress.total}
            currentDateStr={progress.dateStr}
            theme={theme}
          />
        )}

        {/* Tab 1: Config Studio (Quick General Controls + Expandable Complete Controls) */}
        {activeTab === 'studio' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <ConfigEditor
              yamlContent={configYaml}
              onChangeYaml={setConfigYaml}
              theme={theme}
            />

            {/* Quick Teaser Box for Dashboard */}
            {output && (
              <div
                onClick={() => setActiveTab('dashboard')}
                className={`p-4 border ${theme.borderClass} ${theme.cardClass} flex items-center justify-between cursor-pointer hover:border-slate-900 dark:hover:border-slate-100 transition`}
              >
                <div className="flex items-center gap-3">
                  <BarChart2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wider">Latest Simulation Ready</div>
                    <div className={`text-[11px] ${theme.mutedClass}`}>
                      {output.transactions.length.toLocaleString()} completed transactions &bull;{' '}
                      {output.funnel.length.toLocaleString()} customer journey sessions
                    </div>
                  </div>
                </div>
                <span className="text-xs font-semibold">View Full Dashboard &rarr;</span>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Dedicated Full Analytics Dashboard */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <div className="flex items-center justify-between border-b pb-3 border-inherit">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider">Analytics & 90-Day Baseline Diff</h2>
                <p className={`text-xs ${theme.mutedClass} mt-0.5`}>
                  Key performance metrics compared against standard 90-day steady-state supermarket behavior.
                </p>
              </div>
              {output && (
                <span className="text-xs font-mono font-medium opacity-80">
                  {output.transactions.length.toLocaleString()} orders generated
                </span>
              )}
            </div>

            {output ? (
              <SummaryDashboard
                summary={output.summary}
                baselineSummary={baselineOutput ? baselineOutput.summary : null}
                theme={theme}
              />
            ) : (
              <div className={`h-64 border border-dashed ${theme.borderClass} rounded-xl flex items-center justify-center text-xs opacity-50`}>
                Click "Run" to execute simulation and render charts.
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Raw YAML Editor (Syntax highlighting, line numbers, zero blank screen) */}
        {activeTab === 'yaml' && (
          <div className="space-y-6 animate-in fade-in duration-150">
            <RawYamlEditor
              value={configYaml}
              onChange={setConfigYaml}
              theme={theme}
            />
          </div>
        )}
      </main>

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        output={output}
        configYaml={configYaml}
        theme={theme}
      />

      {/* Footer */}
      <footer className={`border-t ${theme.borderClass} py-3.5 px-6 text-center text-xs opacity-60 flex items-center justify-center gap-2`}>
        <span>Creanu Labs Synthetic Commerce Engine</span>
        <span>&bull;</span>
        <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
          <Sparkles className="w-3 h-3" /> Zero Server Compute Cost
        </span>
      </footer>
    </div>
  );
}

export default App;
