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
    cardClass: 'bg-white border-[#cbd5e1] rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.06)]',
    headerClass: 'bg-white/95 border-[#cbd5e1]',
    borderClass: 'border-[#cbd5e1]',
    textClass: 'text-[#0f172a]',
    mutedClass: 'text-[#64748b]',
    accentClass: 'bg-[#0f172a] text-white hover:bg-[#1e293b]',
    buttonClass: 'bg-[#f1f5f9] hover:bg-[#e2e8f0] border-[#94a3b8] text-[#0f172a]',
    inputClass: 'bg-white border-[#94a3b8] text-[#0f172a] focus:border-[#0f172a]',
    chartBarColor: '#0f172a',
    chartLineColor: '#2563eb',
    chartGridColor: '#cbd5e1',
    chartTickColor: '#64748b',
    chartTooltipBg: '#ffffff',
    chartTooltipBorder: '#e2e8f0',
  },
  dark: {
    mode: 'dark',
    name: 'Swiss Dark',
    bodyClass: 'bg-[#0e1013] text-[#f8fafc]',
    cardClass: 'bg-[#15181e] border-[#3a4250] rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.35)]',
    headerClass: 'bg-[#111317]/95 border-[#3a4250]',
    borderClass: 'border-[#3a4250]',
    textClass: 'text-[#f8fafc]',
    mutedClass: 'text-[#9aa3b2]',
    accentClass: 'bg-[#f8fafc] text-[#0e1013] hover:bg-[#e2e8f0]',
    buttonClass: 'bg-[#1b1e25] hover:bg-[#252932] border-[#4a5364] text-[#f8fafc]',
    inputClass: 'bg-[#111317] border-[#4a5364] text-[#f8fafc] focus:border-[#f8fafc]',
    chartBarColor: '#38bdf8',
    chartLineColor: '#60a5fa',
    chartGridColor: '#2c333f',
    chartTickColor: '#8f96a3',
    chartTooltipBg: '#15181e',
    chartTooltipBorder: '#252932',
  },
};
