import { Activity, ArrowLeft, Pause, Play, RotateCcw } from 'lucide-react';
import { SeirChart } from '../components/SeirChart';
import type { NetworkData, SimulationConfig } from '../types';
import { getNetworkStats, runNetworkSeir } from '../utils/networkStats';

export function SimulationRun({ network, config, onBack }: { network: NetworkData | null; config: SimulationConfig; onBack: () => void }) {
  const points = runNetworkSeir(network, config);
  const stats = getNetworkStats(network);
  const population = points[0]
    ? points[0].susceptible + points[0].exposed + points[0].infectious + points[0].recovered
    : 0;

  return (
    <div className="mx-auto grid w-full max-w-6xl items-stretch gap-6 py-8 lg:grid-cols-[1.35fr_0.65fr]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Activity size={24} />
              <h1 className="text-3xl font-normal tracking-tight">Simulatie</h1>
            </div>
            <button className="control-button inline-flex items-center gap-2" onClick={onBack}>
              <ArrowLeft size={16} /> Terug
            </button>
          </div>
          <SeirChart points={points} />
          <p className="mt-3 text-sm text-gray-300">
            Gebaseerd op {stats.nodeCount.toLocaleString('nl-NL')} knopen, {stats.edgeCount.toLocaleString('nl-NL')} verbindingen en beta {config.beta.toFixed(2)}.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="control-button"><Play size={16} /> Start</button>
            <button className="control-button"><Pause size={16} /> Pauze</button>
            <button className="control-button"><RotateCcw size={16} /> Reset</button>
          </div>
        </div>
      </div>

      <div className="liquid-glass rounded-2xl p-6 flex h-full">
        <div className="relative z-10 flex h-full flex-col overflow-hidden">
          <div className="custom-scrollbar flex-1 overflow-y-auto pr-2">
            <div className="space-y-5">
              <div>
                <h2 className="mb-3 text-xl font-medium">Simulatie details</h2>
                <p className="text-sm text-gray-300">
                  De grafiek toont het aandeel van de populatie over de tijd als percentage. Klik op een lijn om deze te selecteren en zie het exacte aantal mensen.
                </p>
              </div>

              <div className="grid gap-3">
                <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                  <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Netwerk</div>
                  <div className="mt-2 text-xl font-semibold text-white">{stats.nodeCount.toLocaleString('nl-NL')} knopen</div>
                  <div className="text-sm text-gray-400">{stats.edgeCount.toLocaleString('nl-NL')} verbindingen</div>
                </div>
                <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                  <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Simulatie</div>
                  <div className="mt-2 text-base font-semibold text-white">Beta: {config.beta.toFixed(2)}</div>
                  <div className="mt-1 text-sm text-gray-400">Incubatie: {config.incubationDays} dagen</div>
                  <div className="text-sm text-gray-400">Besmettelijk: {config.infectiousDays} dagen</div>
                  <div className="text-sm text-gray-400">Herstelkans: {config.recoveryChance}%</div>
                </div>
                <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                  <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Populatie</div>
                  <div className="mt-2 text-xl font-semibold text-white">{population.toLocaleString('nl-NL')}</div>
                  <div className="text-sm text-gray-400">Constante populatiegrootte in de SEIR-simulatie</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
