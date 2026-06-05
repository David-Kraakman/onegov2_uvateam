import React from 'react';
import { Activity, ArrowLeft, Pause, Play, RotateCcw } from 'lucide-react';
import { SeirChart } from '../components/SeirChart';
import type { DataFactor, NetworkData, SimulationConfig } from '../types';
import { calculateFactorMultiplier, getNetworkStats, runNetworkSeir } from '../utils/networkStats';

type SeriesKey = 'susceptible' | 'exposed' | 'infectious' | 'recovered' | 'deaths';

export function SimulationRun({ 
  network, 
  config, 
  dataFactors, 
  onBack 
}: { 
  network: NetworkData | null; 
  config: SimulationConfig; 
  dataFactors: DataFactor[]; 
  onBack: () => void 
}) {
  const [selectedSeries, setSelectedSeries] = React.useState<SeriesKey>('infectious');

  const points = runNetworkSeir(network, config, dataFactors);
  const stats = getNetworkStats(network);
  const factorMultiplier = calculateFactorMultiplier(network, dataFactors);
  const hasProfiles = Boolean(network && network.nodes.some((node) => node.profile));
  
  const selectedSeriesInfo = {
    susceptible: { label: 'Vatbaar', description: 'Sociaal gezien nog vatbare mensen.' },
    exposed: { label: 'Besmet', description: 'Besmet, maar nog niet zelf besmettelijk.' },
    infectious: { label: 'Infectieus', description: 'Actief besmettelijke personen die anderen kunnen besmetten.' },
    recovered: { label: 'Hersteld', description: 'Hersteld en niet langer vatbaar voor nieuwe besmetting.' },
    deaths: { label: 'Doden', description: 'Overleden personen als gevolg van de infectie.' },
  } as const;
  
  const selectedInfo = selectedSeriesInfo[selectedSeries];
  const population = points[0]
    ? points[0].susceptible + points[0].exposed + points[0].infectious + points[0].recovered + points[0].deaths
    : 0;

  return (
    <div className="mx-auto grid w-full max-w-6xl items-stretch gap-6 py-8 lg:grid-cols-[1.2fr_0.8fr]">
      
      {/* LINKER PANEEL: SEIR Grafiek & Controls */}
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
          <SeirChart points={points} selectedSeries={selectedSeries} onSeriesChange={setSelectedSeries} />
          <p className="mt-3 text-sm text-gray-300">
            Gebaseerd op {stats.nodeCount.toLocaleString('nl-NL')} knopen, {stats.edgeCount.toLocaleString('nl-NL')} verbindingen en beta {config.beta.toFixed(0)}%.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="control-button"><Play size={16} /> Start</button>
            <button className="control-button"><Pause size={16} /> Pauze</button>
            <button className="control-button"><RotateCcw size={16} /> Reset</button>
          </div>
        </div>
      </div>

      {/* RECHTER PANEEL: Alleen statistieken en data-overzichten */}
      <div className="liquid-glass rounded-2xl p-6 flex h-full flex-col">
        <div className="relative z-10 flex h-full flex-col overflow-hidden space-y-5">
          
          <div>
            <h2 className="text-xl font-medium">Simulatiestatistieken</h2>
            <p className="text-xs text-gray-400 mt-1">Live overzicht van de epidemische indicatoren.</p>
          </div>

          <div className="custom-scrollbar flex-1 overflow-y-auto pr-2">
            <div className="grid gap-3 pt-1">
              
              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Geselecteerde serie</div>
                <div className="mt-2 text-xl font-semibold text-white">{selectedInfo.label}</div>
                <div className="mt-2 text-sm text-gray-400">{selectedInfo.description}</div>
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Laatste dag</div>
                    <div className="mt-2 text-lg font-semibold text-white">
                      {points[points.length - 1]?.[selectedSeries]?.toLocaleString('nl-NL') ?? 0}
                    </div>
                    <div className="text-xs text-slate-400">
                      {population > 0 ? ((points[points.length - 1]?.[selectedSeries] / population) * 100).toFixed(1) : 0}% van populatie
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Dag</div>
                    <div className="mt-2 text-lg font-semibold text-white">{points[points.length - 1]?.day ?? 0}</div>
                  </div>
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Gemiddeld effect</div>
                <div className="mt-2 text-xl font-semibold text-white">{factorMultiplier.toFixed(2)}×</div>
                <div className="text-sm text-gray-400">{hasProfiles ? 'Profielen gebruikt voor datafactoren' : 'Geen profielen beschikbaar: generieke gemiddelden gebruikt'}</div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Netwerk structuur</div>
                <div className="mt-2 text-xl font-semibold text-white">{stats.nodeCount.toLocaleString('nl-NL')} knopen</div>
                <div className="text-sm text-gray-400">{stats.edgeCount.toLocaleString('nl-NL')} verbindingen</div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-[0.24em] text-gray-500">Totale Populatie</div>
                <div className="mt-2 text-xl font-semibold text-white">{population.toLocaleString('nl-NL')}</div>
                <div className="text-sm text-gray-400">Constante populatiegrootte binnen dit scenario</div>
              </div>

            </div>
          </div>

        </div>
      </div>

    </div>
  );
}