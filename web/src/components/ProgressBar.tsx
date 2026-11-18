import React from 'react';
import { ThemeConfig } from '../types/theme';

interface ProgressBarProps {
  currentDay: number;
  totalDays: number;
  currentDateStr: string;
  theme: ThemeConfig;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  currentDay,
  totalDays,
  currentDateStr,
  theme,
}) => {
  const pct = Math.min(100, Math.round((currentDay / totalDays) * 100));

  return (
    <div className={`p-4 border ${theme.borderClass} ${theme.cardClass} shadow-md space-y-2 animate-in fade-in duration-150`}>
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-semibold">
            Simulating Day {currentDay} of {totalDays}
          </span>
          <span className="font-mono text-[11px] opacity-70 px-1.5 py-0.5 rounded border border-inherit">
            {currentDateStr}
          </span>
        </div>
        <span className="font-bold font-mono text-emerald-500">{pct}%</span>
      </div>
      <div className="w-full bg-black/10 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
        <div
          className="bg-emerald-500 h-full transition-all duration-100 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};
