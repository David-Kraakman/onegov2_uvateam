import { BarChart3, Download } from 'lucide-react';
import { NetworkCanvas } from '../components/NetworkCanvas';

export function NetworkGeneration() {
  return (
    <div className="mx-auto grid w-full max-w-6xl items-center gap-6 py-8 lg:grid-cols-[1fr_320px]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10 h-full">
          <h1 className="mb-4 text-3xl font-normal tracking-tight">Netwerk genereren</h1>
          <NetworkCanvas />
        </div>
      </div>
      <aside className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h2 className="mb-5 flex items-center gap-2 text-lg font-medium"><BarChart3 size={18} /> Netwerkstatistieken</h2>
          {[
            ['Knopen', '1.248'],
            ['Verbindingen', '7.931'],
            ['Gemiddelde graad', '12,7'],
            ['Clustering', '0,42'],
            ['Huishoudcontacten', '38%'],
          ].map(([label, value]) => (
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3 text-sm" key={label}>
              <span className="text-gray-300">{label}</span>
              <span className="font-medium">{value}</span>
            </div>
          ))}
          <button className="liquid-glass mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-medium transition hover:text-gray-300">
            <Download size={16} /> Download netwerk (JSON/CSV)
          </button>
        </div>
      </aside>
    </div>
  );
}
