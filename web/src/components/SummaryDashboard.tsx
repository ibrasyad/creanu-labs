import React, { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';
import { TrendingUp, ShoppingCart, DollarSign, Percent, Award } from 'lucide-react';
import { SimulationSummary } from '../types/simulation';
import { ThemeConfig } from '../types/theme';

interface SummaryDashboardProps {
  summary: SimulationSummary;
  baselineSummary: SimulationSummary | null;
  theme: ThemeConfig;
}

type AggregationInterval = 'daily' | 'weekly' | 'monthly' | 'yearly';

export const SummaryDashboard: React.FC<SummaryDashboardProps> = ({
  summary,
  baselineSummary,
  theme,
}) => {
  const [interval, setInterval] = useState<AggregationInterval>('daily');

  // Format Indonesian Rupiah
  const formatIDR = (val: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  // User simulation days count vs baseline days count
  const userDays = Math.max(1, summary.daily_metrics.length);
  const baselineDays = baselineSummary ? Math.max(1, baselineSummary.daily_metrics.length) : 90;

  // Normalized Daily Averages
  const userDailyRev = summary.total_revenue / userDays;
  const baselineDailyRev = baselineSummary ? baselineSummary.total_revenue / baselineDays : 0;

  const userDailyOrders = summary.total_transactions / userDays;
  const baselineDailyOrders = baselineSummary ? baselineSummary.total_transactions / baselineDays : 0;

  // Compute Delta %
  const computeDelta = (current: number, baseline: number) => {
    if (!baseline || baseline === 0) return null;
    const pct = ((current - baseline) / baseline) * 100;
    const sign = pct >= 0 ? '+' : '';
    return {
      text: `${sign}${pct.toFixed(1)}% vs 90d baseline`,
      isPositive: pct >= 0,
    };
  };

  const revenueDelta = baselineSummary ? computeDelta(userDailyRev, baselineDailyRev) : null;
  const ordersDelta = baselineSummary ? computeDelta(userDailyOrders, baselineDailyOrders) : null;
  const aovDelta = baselineSummary ? computeDelta(summary.average_order_value, baselineSummary.average_order_value) : null;
  const convDelta = baselineSummary ? computeDelta(summary.overall_conversion_rate, baselineSummary.overall_conversion_rate) : null;

  // Prepare Funnel Data for BarChart
  const funnelStages = ['landing_page', 'product_view', 'add_to_cart', 'checkout', 'paid'];
  const funnelData = funnelStages.map((stage) => {
    const count = summary.funnel_breakdown[stage] || 0;
    const baseCount = summary.funnel_breakdown['landing_page'] || 1;
    return {
      stage: stage.replace('_', ' ').toUpperCase(),
      sessions: count,
      dropoffPct: Math.round((count / baseCount) * 100),
    };
  });

  // Aggregation of Revenue Data by Interval
  const aggregatedRevenueData = useMemo(() => {
    const raw = summary.daily_metrics;
    if (raw.length === 0) return [];

    if (interval === 'daily') {
      return raw.map((d) => ({
        label: d.date.slice(5),
        revenue: d.gross_revenue,
        transactions: d.transactions,
      }));
    }

    if (interval === 'weekly') {
      const weeks: { label: string; revenue: number; transactions: number }[] = [];
      let currentWeekRev = 0;
      let currentWeekTrx = 0;
      let weekNumber = 1;

      for (let i = 0; i < raw.length; i++) {
        currentWeekRev += raw[i].gross_revenue;
        currentWeekTrx += raw[i].transactions;
        if ((i + 1) % 7 === 0 || i === raw.length - 1) {
          weeks.push({
            label: `W${weekNumber}`,
            revenue: currentWeekRev,
            transactions: currentWeekTrx,
          });
          currentWeekRev = 0;
          currentWeekTrx = 0;
          weekNumber++;
        }
      }
      return weeks;
    }

    if (interval === 'monthly') {
      const monthMap = new Map<string, { revenue: number; transactions: number }>();
      for (const d of raw) {
        const monthKey = d.date.slice(0, 7); // "YYYY-MM"
        const existing = monthMap.get(monthKey) || { revenue: 0, transactions: 0 };
        existing.revenue += d.gross_revenue;
        existing.transactions += d.transactions;
        monthMap.set(monthKey, existing);
      }
      return Array.from(monthMap.entries()).map(([month, data]) => ({
        label: month,
        revenue: data.revenue,
        transactions: data.transactions,
      }));
    }

    // Yearly
    const yearMap = new Map<string, { revenue: number; transactions: number }>();
    for (const d of raw) {
      const yearKey = d.date.slice(0, 4); // "YYYY"
      const existing = yearMap.get(yearKey) || { revenue: 0, transactions: 0 };
      existing.revenue += d.gross_revenue;
      existing.transactions += d.transactions;
      yearMap.set(yearKey, existing);
    }
    return Array.from(yearMap.entries()).map(([year, data]) => ({
      label: year,
      revenue: data.revenue,
      transactions: data.transactions,
    }));
  }, [summary.daily_metrics, interval]);

  return (
    <div className="space-y-6">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Gross Revenue */}
        <div className={`p-5 border ${theme.borderClass} ${theme.cardClass} flex flex-col justify-between`}>
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider mb-2 opacity-70">
            <span>Total Revenue</span>
            <DollarSign className="w-4 h-4 opacity-80" />
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight">{formatIDR(summary.total_revenue)}</div>
          {revenueDelta && (
            <div className={`text-xs mt-2 font-medium ${revenueDelta.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
              {revenueDelta.text} (daily pace)
            </div>
          )}
        </div>

        {/* Completed Orders */}
        <div className={`p-5 border ${theme.borderClass} ${theme.cardClass} flex flex-col justify-between`}>
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider mb-2 opacity-70">
            <span>Completed Orders</span>
            <ShoppingCart className="w-4 h-4 opacity-80" />
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight">
            {summary.total_transactions.toLocaleString()}
          </div>
          {ordersDelta && (
            <div className={`text-xs mt-2 font-medium ${ordersDelta.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
              {ordersDelta.text} (daily pace)
            </div>
          )}
        </div>

        {/* Funnel Conversion */}
        <div className={`p-5 border ${theme.borderClass} ${theme.cardClass} flex flex-col justify-between`}>
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider mb-2 opacity-70">
            <span>Funnel Conversion</span>
            <Percent className="w-4 h-4 opacity-80" />
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight">
            {(summary.overall_conversion_rate * 100).toFixed(2)}%
          </div>
          {convDelta && (
            <div className={`text-xs mt-2 font-medium ${convDelta.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
              {convDelta.text}
            </div>
          )}
        </div>

        {/* Average Order Value */}
        <div className={`p-5 border ${theme.borderClass} ${theme.cardClass} flex flex-col justify-between`}>
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider mb-2 opacity-70">
            <span>Average Order Value</span>
            <TrendingUp className="w-4 h-4 opacity-80" />
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight">{formatIDR(summary.average_order_value)}</div>
          {aovDelta && (
            <div className={`text-xs mt-2 font-medium ${aovDelta.isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
              {aovDelta.text}
            </div>
          )}
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Journey BarChart */}
        <div className={`p-5 border ${theme.borderClass} ${theme.cardClass} flex flex-col`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider">Conversion Drop-off Journey</h3>
              <p className={`text-xs ${theme.mutedClass}`}>Surviving sessions across stages</p>
            </div>
            <span className="text-xs font-mono font-semibold opacity-80">
              {funnelData[funnelData.length - 1]?.dropoffPct}% End-to-End
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="stage" tick={{ fill: theme.chartTickColor, fontSize: 10 }} />
                <YAxis tick={{ fill: theme.chartTickColor, fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: theme.chartTooltipBg, borderColor: theme.chartTooltipBorder, borderRadius: '8px' }}
                  itemStyle={{ color: theme.chartBarColor }}
                />
                <Bar dataKey="sessions" fill={theme.chartBarColor} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Revenue Timeline with Aggregation Toggles */}
        <div className={`p-5 border ${theme.borderClass} ${theme.cardClass} flex flex-col`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider">Revenue Trend</h3>
              <p className={`text-xs ${theme.mutedClass}`}>Aggregate revenue across intervals</p>
            </div>

            {/* Aggregation Toggles: Daily, Weekly, Monthly, Yearly */}
            <div className="flex items-center gap-1 p-0.5 rounded border border-inherit bg-black/5 dark:bg-white/5 text-[11px]">
              {(['daily', 'weekly', 'monthly', 'yearly'] as AggregationInterval[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setInterval(mode)}
                  className={`px-2 py-0.5 rounded capitalize font-medium transition ${
                    interval === mode ? theme.accentClass : 'opacity-70 hover:opacity-100'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={aggregatedRevenueData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.chartGridColor} />
                <XAxis dataKey="label" tick={{ fill: theme.chartTickColor, fontSize: 9 }} />
                <YAxis tick={{ fill: theme.chartTickColor, fontSize: 9 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: theme.chartTooltipBg, borderColor: theme.chartTooltipBorder, borderRadius: '8px' }}
                  formatter={(value: any) => [formatIDR(Number(value)), 'Revenue']}
                />
                <Line type="monotone" dataKey="revenue" stroke={theme.chartLineColor} strokeWidth={2} dot={{ r: 2.5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Products Table */}
      <div className={`p-5 border ${theme.borderClass} ${theme.cardClass}`}>
        <div className="flex items-center gap-2 mb-4">
          <Award className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider">Top Selling Grocery Items</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className={`border-b ${theme.borderClass} opacity-60 font-mono`}>
                <th className="py-2 px-3 font-semibold">Rank</th>
                <th className="py-2 px-3 font-semibold">Product Name</th>
                <th className="py-2 px-3 font-semibold text-right">Units Sold</th>
                <th className="py-2 px-3 font-semibold text-right">Total Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-inherit/40">
              {summary.top_products.map(([prod, qty, rev], idx) => (
                <tr key={prod} className="hover:bg-black/5 dark:hover:bg-white/5">
                  <td className="py-2.5 px-3 font-mono font-bold opacity-70">#{idx + 1}</td>
                  <td className="py-2.5 px-3 font-medium capitalize">{prod}</td>
                  <td className="py-2.5 px-3 text-right font-mono opacity-80">{qty.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold">{formatIDR(rev)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
