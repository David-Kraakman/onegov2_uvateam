import { Activity, Map, Pause, Play, RotateCcw } from 'lucide-react';
import { SeirChart } from '../components/SeirChart';
import type { NetworkData, SimulationConfig } from '../types';
import { getNetworkStats, runNetworkSeir } from '../utils/networkStats';

export function SimulationRun({ network, config }: { network: NetworkData | null; config: SimulationConfig }) {
  const points = runNetworkSeir(network, config);
  const stats = getNetworkStats(network);

  return (
    <div className="mx-auto grid w-full max-w-6xl items-center gap-6 py-8 lg:grid-cols-[1fr_0.9fr]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h1 className="mb-5 flex items-center gap-2 text-3xl font-normal tracking-tight"><Activity size={24} /> Simulatie</h1>
          <SeirChart points={points} />
          <p className="mt-3 text-sm text-gray-300">
            Gebaseerd op {stats.nodeCount.toLocaleString('nl-NL')} knopen, {stats.edgeCount.toLocaleString('nl-NL')} verbindingen en beta {config.beta.toFixed(2)}.
          </p>
          <div className="mt-5 flex gap-3">
            <button className="control-button"><Play size={16} /> Start</button>
            <button className="control-button"><Pause size={16} /> Pauze</button>
            <button className="control-button"><RotateCcw size={16} /> Reset</button>
          </div>
        </div>
      </div>
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h2 className="mb-5 flex items-center gap-2 text-xl font-medium"><Map size={20} /> Transmissieverdeling in Utrecht</h2>
          <div className="relative h-[420px] overflow-hidden rounded-lg border border-white/10 bg-black/35">
            {Array.from({ length: 26 }, (_, i) => (
              <span key={i} className="absolute rounded-full bg-white" style={{ left: `${8 + (i * 31) % 84}%`, top: `${12 + (i * 47) % 74}%`, width: `${10 + (i % 5) * 8}px`, height: `${10 + (i % 5) * 8}px`, opacity: Math.min(0.85, 0.12 + stats.meanDegree / 80 + (i % 6) * 0.05) }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
