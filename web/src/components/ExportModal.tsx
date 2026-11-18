import React, { useState } from 'react';
import JSZip from 'jszip';
import { X, Download, FileText, Archive, CheckCircle2 } from 'lucide-react';
import { SimulationOutput } from '../types/simulation';
import { ThemeConfig } from '../types/theme';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  output: SimulationOutput | null;
  configYaml: string;
  theme: ThemeConfig;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  output,
  configYaml,
  theme,
}) => {
  const [isZipping, setIsZipping] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  if (!isOpen || !output) return null;

  const generateCSV = (headers: string[], rows: (string | number)[][]): string => {
    const headerLine = headers.join(',');
    const bodyLines = rows.map((r) => r.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','));
    return [headerLine, ...bodyLines].join('\n');
  };

  const getUserCSV = () =>
    generateCSV(
      ['tier', 'user_id', 'city', 'gender', 'acquisition_channel', 'registered_date', 'last_active_date'],
      output.users.map((u) => [
        u.tier,
        u.user_id,
        u.city,
        u.gender,
        u.acquisition_channel,
        u.registered_date,
        u.last_active_date,
      ])
    );

  const getTrxCSV = () =>
    generateCSV(
      ['session_id', 'user_id', 'trx_id', 'date', 'tier', 'total_price'],
      output.transactions.map((t) => [t.session_id, t.user_id, t.trx_id, t.date, t.tier, t.total_price])
    );

  const getItemCSV = () =>
    generateCSV(
      ['trx_id', 'user_id', 'tier', 'date', 'product', 'quantity', 'unit_price', 'total_price'],
      output.transaction_items.map((i) => [
        i.trx_id,
        i.user_id,
        i.tier,
        i.date,
        i.product,
        i.quantity,
        i.unit_price,
        i.total_price,
      ])
    );

  const getFunnelCSV = () =>
    generateCSV(
      ['session_id', 'tier', 'user_id', 'activity', 'activity_datetime'],
      output.funnel.map((f) => [f.session_id, f.tier, f.user_id, f.activity, f.activity_datetime])
    );

  const getCatalogCSV = () =>
    generateCSV(
      ['category', 'subcategory', 'product', 'base_price'],
      output.catalog.map((c) => [c.category, c.subcategory, c.product, c.base_price])
    );

  const triggerDownload = (filename: string, content: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setDownloadSuccess(filename);
    setTimeout(() => setDownloadSuccess(null), 3000);
  };

  const downloadAllZip = async () => {
    setIsZipping(true);
    try {
      const zip = new JSZip();
      zip.file('user.csv', getUserCSV());
      zip.file('transaction.csv', getTrxCSV());
      zip.file('transaction_item.csv', getItemCSV());
      zip.file('funnel.csv', getFunnelCSV());
      zip.file('catalog.csv', getCatalogCSV());
      zip.file('simulation_config.yaml', configYaml);

      const blob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `creanu-labs-dataset-${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setDownloadSuccess('dataset.zip');
      setTimeout(() => setDownloadSuccess(null), 3000);
    } catch (err) {
      console.error('ZIP packaging failed:', err);
    } finally {
      setIsZipping(false);
    }
  };

  const tables = [
    { name: 'user.csv', count: output.users.length, desc: 'Registered customer demographics', getter: getUserCSV },
    { name: 'transaction.csv', count: output.transactions.length, desc: 'Session headers & order totals', getter: getTrxCSV },
    { name: 'transaction_item.csv', count: output.transaction_items.length, desc: 'Product line items & basket quantities', getter: getItemCSV },
    { name: 'funnel.csv', count: output.funnel.length, desc: 'Customer session journey logs', getter: getFunnelCSV },
    { name: 'catalog.csv', count: output.catalog.length, desc: 'Product categories & base prices', getter: getCatalogCSV },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className={`border ${theme.borderClass} ${theme.cardClass} w-full max-w-xl shadow-2xl overflow-hidden flex flex-col`}>
        {/* Header */}
        <div className={`px-6 py-4 border-b ${theme.borderClass} flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <Archive className="w-4 h-4 opacity-80" />
            <h2 className="font-bold text-sm uppercase tracking-wide">Export Dataset Packages</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded opacity-60 hover:opacity-100 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {downloadSuccess && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Downloaded <strong>{downloadSuccess}</strong> successfully!</span>
            </div>
          )}

          {/* Master 1-Click ZIP Button */}
          <div className={`p-4 rounded border border-inherit bg-black/5 dark:bg-white/5 flex items-center justify-between`}>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-bold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">Complete Dataset ZIP Bundle</h3>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded font-mono font-medium">100% Full Export</span>
              </div>
              <p className={`text-[11px] ${theme.mutedClass} mt-0.5`}>All 5 CSV tables plus configuration YAML without row caps or truncation.</p>
            </div>
            <button
              onClick={downloadAllZip}
              disabled={isZipping}
              className={`px-3.5 py-1.5 text-xs font-bold rounded shadow-sm flex items-center gap-1.5 transition active:scale-95 disabled:opacity-50 ${theme.accentClass}`}
            >
              {isZipping ? <span>Zipping...</span> : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Download ZIP</span>
                </>
              )}
            </button>
          </div>

          {/* Tables */}
          <div className="space-y-1.5">
            <span className={`text-[11px] font-bold uppercase tracking-wider block ${theme.mutedClass}`}>Individual CSV Tables</span>
            <div className={`divide-y divide-inherit border ${theme.borderClass} rounded overflow-hidden`}>
              {tables.map((t) => (
                <div key={t.name} className="px-4 py-2.5 flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/5">
                  <div className="flex items-center gap-2.5">
                    <FileText className="w-4 h-4 opacity-60" />
                    <div>
                      <div className="text-xs font-mono font-medium">{t.name}</div>
                      <div className={`text-[10px] ${theme.mutedClass}`}>{t.desc} &bull; {t.count.toLocaleString()} rows</div>
                    </div>
                  </div>
                  <button
                    onClick={() => triggerDownload(t.name, t.getter(), 'text/csv')}
                    className={`p-1.5 rounded border ${theme.buttonClass} transition`}
                    title={`Download ${t.name}`}
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={`px-6 py-3 border-t ${theme.borderClass} flex justify-end bg-black/5 dark:bg-white/5`}>
          <button
            onClick={onClose}
            className={`px-3 py-1 text-xs font-medium rounded border ${theme.buttonClass}`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
