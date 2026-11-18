export type ThemeMode = 'light' | 'dark';

export interface ThemeConfig {
  mode: ThemeMode;
  name: string;
  bodyClass: string;
  cardClass: string;
  headerClass: string;
  borderClass: string;
  textClass: string;
  mutedClass: string;
  accentClass: string;
  buttonClass: string;
  inputClass: string;
  chartBarColor: string;
  chartLineColor: string;
  chartGridColor: string;
  chartTickColor: string;
  chartTooltipBg: string;
  chartTooltipBorder: string;
}

export const SWISS_THEMES: Record<ThemeMode, ThemeConfig> = {
  light: {
    mode: 'light',
    name: 'Swiss Light',
    bodyClass: 'bg-[#f8f9fa] text-[#0f172a]',
    cardClass: 'bg-white border-[#e2e8f0] rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.04)]',
    headerClass: 'bg-white/95 border-[#e2e8f0]',
    borderClass: 'border-[#e2e8f0]',
    textClass: 'text-[#0f172a]',
    mutedClass: 'text-[#64748b]',
    accentClass: 'bg-[#0f172a] text-white hover:bg-[#1e293b]',
    buttonClass: 'bg-[#f1f5f9] hover:bg-[#e2e8f0] border-[#cbd5e1] text-[#0f172a]',
    inputClass: 'bg-[#f8f9fa] border-[#cbd5e1] text-[#0f172a] focus:border-[#0f172a]',
    chartBarColor: '#0f172a',
    chartLineColor: '#2563eb',
    chartGridColor: '#e2e8f0',
    chartTickColor: '#64748b',
    chartTooltipBg: '#ffffff',
    chartTooltipBorder: '#e2e8f0',
  },
  dark: {
    mode: 'dark',
    name: 'Swiss Dark',
    bodyClass: 'bg-[#0e1013] text-[#f8fafc]',
    cardClass: 'bg-[#15181e] border-[#252932] rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.2)]',
    headerClass: 'bg-[#111317]/95 border-[#22262f]',
    borderClass: 'border-[#252932]',
    textClass: 'text-[#f8fafc]',
    mutedClass: 'text-[#8f96a3]',
    accentClass: 'bg-[#f8fafc] text-[#0e1013] hover:bg-[#e2e8f0]',
    buttonClass: 'bg-[#1b1e25] hover:bg-[#252932] border-[#2e333e] text-[#f8fafc]',
    inputClass: 'bg-[#111317] border-[#2e333e] text-[#f8fafc] focus:border-[#f8fafc]',
    chartBarColor: '#38bdf8',
    chartLineColor: '#60a5fa',
    chartGridColor: '#1f242d',
    chartTickColor: '#8f96a3',
    chartTooltipBg: '#15181e',
    chartTooltipBorder: '#252932',
  },
};
