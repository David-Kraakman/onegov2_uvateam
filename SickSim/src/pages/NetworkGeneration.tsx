import React from 'react';
import { BarChart3, Download } from 'lucide-react';
import { NetworkCanvas } from '../components/NetworkCanvas';
import type { DataFactor, NetworkData } from '../types';
import { generateSyntheticNetwork } from '../utils/generateNetwork';
import { getNetworkStats } from '../utils/networkStats';

type NetworkGenerationProps = {
  network: NetworkData | null;
  onNetworkGenerated: (network: NetworkData) => void;
  dataFactors: DataFactor[];
};

// Wiskundige helper om risicoscore te bepalen op basis van de slider-grenzen
function mapDynamicRisk(val: number, domainMin: number, domainMax: number, targetMin: number, targetMax: number, invert = false): number {
  let ratio = (val - domainMin) / (domainMax - domainMin);
  ratio = Math.max(0, Math.min(1, ratio));
  if (invert) ratio = 1 - ratio; 
  return targetMin + (ratio * (targetMax - targetMin));
}

export function NetworkGeneration({ network, onNetworkGenerated, dataFactors }: NetworkGenerationProps) {
  const [generationStatus, setGenerationStatus] = React.useState('');
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);

  const stats = network 
    ? getNetworkStats(network) 
    : { nodeCount: 0, edgeCount: 0, meanDegree: 0, density: 0, largestDegree: 0 };

  const rows = [
    ['Bronbestand', network?.fileName ?? 'Geen netwerk actief'],
    ['Aantal Agents', stats.nodeCount.toLocaleString('nl-NL')],
    ['Verbindingen', stats.edgeCount.toLocaleString('nl-NL')],
    ['Gemiddelde graad', stats.meanDegree.toLocaleString('nl-NL', { maximumFractionDigits: 2 })],
    ['Netwerkdichtheid', stats.density.toLocaleString('nl-NL', { maximumFractionDigits: 4 })],
    ['Hoogste graad', stats.largestDegree.toLocaleString('nl-NL')],
  ];

  // Bereken de exacte risicofactor van de geselecteerde agent
  const getAgeGroup = (leeftijd: number) => {
    if (leeftijd <= 14) return '0-14';
    if (leeftijd <= 24) return '15-24';
    if (leeftijd <= 44) return '25-44';
    if (leeftijd <= 64) return '45-64';
    return '65+';
  };

  const getSelectedNodeRisk = () => {
    if (!network || !selectedNodeId) return null;
    const node = network.nodes.find(n => n.id === selectedNodeId);
    const p = node?.profile;
    if (!p) return null;

    let totalRisk = 0;
    let activeFactorsCount = 0;
    const getFactor = (keyword: string) => dataFactors.find(f => f.label.toLowerCase().includes(keyword.toLowerCase()));

    const fBevolking = getFactor('bevolkingsomvang');
    if (fBevolking?.enabled) {
      totalRisk += mapDynamicRisk(p.bevolkingsomvang, 800, 14000, fBevolking.minFactor, fBevolking.maxFactor);
      activeFactorsCount++;
    }

    const fBezettingsgraad = getFactor('bezettingsgraad');
    if (fBezettingsgraad?.enabled) {
      totalRisk += mapDynamicRisk(p.bezettingsgraadWoning, 1.2, 3.6, fBezettingsgraad.minFactor, fBezettingsgraad.maxFactor);
      activeFactorsCount++;
    }

    const fInkomen = getFactor('inkomen');
    if (fInkomen?.enabled) {
      totalRisk += mapDynamicRisk(p.gemiddeldBestedbaarInkomen, 24000, 68000, fInkomen.minFactor, fInkomen.maxFactor, true);
      activeFactorsCount++;
    }

    const fStedelijkheid = getFactor('stedelijkheidsgraad');
    if (fStedelijkheid?.enabled) {
      totalRisk += mapDynamicRisk(p.stedelijkheidsgraad, 1, 5, fStedelijkheid.minFactor, fStedelijkheid.maxFactor, true);
      activeFactorsCount++;
    }

    const fNietWesters = getFactor('niet-westerse');
    if (fNietWesters?.enabled) {
      totalRisk += mapDynamicRisk(p.aandeelNietWesterseAchtergrond, 0, 50, fNietWesters.minFactor, fNietWesters.maxFactor);
      activeFactorsCount++;
    }

    const fLeeftijd = getFactor('leeftijd');
    if (fLeeftijd?.enabled) {
      const leeftijd = p.leeftijd ?? 0;
      const ageRisk = leeftijd <= 14 || leeftijd >= 65
        ? fLeeftijd.maxFactor
        : leeftijd <= 24 || leeftijd >= 45
          ? (fLeeftijd.minFactor + fLeeftijd.maxFactor) / 2
          : fLeeftijd.minFactor;
      totalRisk += ageRisk;
      activeFactorsCount++;
    }

    const fOpleiding = getFactor('opleidingsniveau');
    if (fOpleiding?.enabled) {
      totalRisk += mapDynamicRisk(p.opleidingsniveau.laag, 10, 40, fOpleiding.minFactor, fOpleiding.maxFactor);
      activeFactorsCount++;
    }

    const fWoningtype = getFactor('woningtype');
    if (fWoningtype?.enabled) {
      const typeFactor = p.woningtype === 'appartement' ? fWoningtype.maxFactor 
                       : (p.woningtype === 'rijtjeshuis' ? (fWoningtype.minFactor + fWoningtype.maxFactor)/2 
                       : fWoningtype.minFactor);
      totalRisk += typeFactor;
      activeFactorsCount++;
    }

    if (activeFactorsCount === 0) return 1.0;
    return totalRisk / activeFactorsCount;
  };

  const activeRiskScore = getSelectedNodeRisk();

  const downloadJson = () => {
    if (!network) {
      setGenerationStatus('Genereer eerst een netwerk voordat je deze downloadt.');
      return;
    }
    const content = JSON.stringify({ nodes: network.nodes, edges: network.edges }, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = network.fileName.endsWith('.json') ? network.fileName : `${network.fileName.split('.')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    setGenerationStatus(`${link.download} gedownload.`);
  };

  const escapeCsvValue = (value: string | number | undefined | null) => {
    if (value === undefined || value === null) return '""';
    return `"${String(value).replace(/"/g, '""')}"`;
  };

  const downloadCsv = () => {
    if (!network) {
      setGenerationStatus('Genereer of upload eerst een netwerk.');
      return;
    }

    const headers = [
      'id', 'label', 'buurtcode', 'wijkcode', 'bevolkingsomvang',
      'leeftijd', 'leeftijdsgroep',
      'huishoudgrootte', 'huishoudenSamenstelling', 'aandeelNietWesterseAchtergrond',
      'woningtype', 'bezettingsgraadWoning', 'gemiddeldBestedbaarInkomen', 'stedelijkheidsgraad',
      'opleidingsniveau_laag', 'opleidingsniveau_midden', 'opleidingsniveau_hoog',
      'rwzi_id', 'rwzi_naam', 'rwzi_locatie', 'rwzi_capaciteit',
      'catchment_oppervlakteKm2', 'catchment_aansluitingen',
      'landgebruik_woongebied', 'landgebruik_industrie', 'landgebruik_agrarisch',
      'nabijheidHavenKm'
    ];

    const csvRows = [headers.join(',')];

    network.nodes.forEach((node) => {
      const p = node.profile;
      if (!p) return;
      csvRows.push([
        escapeCsvValue(node.id), escapeCsvValue(node.label), escapeCsvValue(p.buurtcode), escapeCsvValue(p.wijkcode), escapeCsvValue(p.bevolkingsomvang),
        escapeCsvValue(p.leeftijd), escapeCsvValue(getAgeGroup(p.leeftijd ?? 0)),
        escapeCsvValue(p.huishoudgrootte), escapeCsvValue(p.huishoudenSamenstelling), escapeCsvValue(p.aandeelNietWesterseAchtergrond), escapeCsvValue(p.woningtype), escapeCsvValue(p.bezettingsgraadWoning), escapeCsvValue(p.gemiddeldBestedbaarInkomen), escapeCsvValue(p.stedelijkheidsgraad),
        escapeCsvValue(p.opleidingsniveau.laag), escapeCsvValue(p.opleidingsniveau.midden), escapeCsvValue(p.opleidingsniveau.hoog),
        escapeCsvValue(p.rwzi.id), escapeCsvValue(p.rwzi.naam), escapeCsvValue(p.rwzi.locatie), escapeCsvValue(p.rwzi.capaciteit),
        escapeCsvValue(p.catchment.oppervlakteKm2), escapeCsvValue(p.catchment.aansluitingen),
        escapeCsvValue(p.landgebruik.woongebied), escapeCsvValue(p.landgebruik.industrie), escapeCsvValue(p.landgebruik.agrarisch),
        escapeCsvValue(p.nabijheidHavenKm),
      ].join(','));
    });

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${network.fileName.split('.')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    setGenerationStatus(`${link.download} gedownload.`);
  };

  React.useEffect(() => {
    setSelectedNodeId(null);
  }, [network]);

  return (
    <div className="mx-auto grid w-full max-w-6xl items-stretch gap-6 py-8 lg:grid-cols-[1fr_340px]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10 h-full">
          <h1 className="mb-4 text-3xl font-normal tracking-tight">Netwerk genereren</h1>
          <NetworkCanvas network={network} selectedNodeId={selectedNodeId ?? undefined} onNodeSelect={setSelectedNodeId} dataFactors={dataFactors} />
          <p className="mt-4 text-sm text-gray-300">Klik op een agent om de specifieke parameters in te zien.</p>
        </div>
      </div>
      
      <aside className="liquid-glass rounded-2xl p-6 h-full">
        <div className="relative z-10 flex h-full flex-col">
          <div className="custom-scrollbar flex-1 overflow-y-auto pr-2">
            <h2 className="mb-5 flex items-center gap-2 text-lg font-medium"><BarChart3 size={18} /> Netwerkstatistieken</h2>
            {rows.map(([label, value]) => (
              <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3 text-sm" key={label}>
                <span className="text-gray-300">{label}</span>
                <span className="max-w-[160px] truncate text-right font-medium">{value}</span>
              </div>
            ))}

            <div className="mt-6 rounded-2xl border border-white/10 bg-black/25 p-4 text-sm text-gray-300">
              <h3 className="mb-3 text-base font-semibold text-white">Geselecteerde Agent</h3>
              {network && selectedNodeId ? (
                (() => {
                  const node = network.nodes.find((item) => item.id === selectedNodeId);
                  const p = node?.profile;
                  if (!p) return <p className="text-gray-400">Geen profieldata aanwezig.</p>;

                  return (
                    <div className="space-y-4 text-xs">
                      {/* LIVE RISICO FACTOR BADGE */}
                      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3">
                        <div className="text-[10px] uppercase tracking-wider text-red-400 font-medium">Berekend transmissierisico</div>
                        <div className="text-lg font-bold text-white mt-0.5">{activeRiskScore ? `${activeRiskScore.toFixed(2)}×` : '1.00×'}</div>
                      </div>

                      <div className="rounded-xl border border-white/10 bg-black/20 p-3">
                        <div className="text-sm font-medium text-white">{node.label}</div>
                        <div className="text-gray-400">Agent ID: {node.id}</div>
                        <div className="text-gray-400">Buurt: {p.buurtcode} | Wijk: {p.wijkcode}</div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                          <span className="font-semibold text-white block mb-1">🧍 Agentgegevens</span>
                          <div>Woningtype: {p.woningtype}</div>
                          <div>Huishoudgrootte: {p.huishoudgrootte}</div>
                          <div>Huishoudensamenstelling: {p.huishoudenSamenstelling}</div>
                          <div className="mt-2 text-[11px] text-gray-400">
                            Leeftijd: {p.leeftijd} jaar | Leeftijdsgroep: {getAgeGroup(p.leeftijd ?? 0)}
                          </div>
                        </div>

                        <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                          <span className="font-semibold text-white block mb-1">📍 Wijkcontext</span>
                          <div>Buurtomvang: {p.bevolkingsomvang} inwoners</div>
                          <div>Inkomen: €{p.gemiddeldBestedbaarInkomen.toLocaleString('nl-NL')}</div>
                          <div>Stedelijkheidsgraad: {p.stedelijkheidsgraad}</div>
                          <div>Niet-westerse achtergrond: {p.aandeelNietWesterseAchtergrond}%</div>
                          <div className="mt-1 text-[11px] text-gray-400">
                            Opleiding: laag {p.opleidingsniveau.laag}% / midden {p.opleidingsniveau.midden}% / hoog {p.opleidingsniveau.hoog}%
                          </div>
                        </div>

                        <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                          <span className="font-semibold text-white block mb-1">🌍 Omgeving</span>
                          <div>{p.rwzi.id}: {p.rwzi.naam}</div>
                          <div>RWZI capaciteit: {p.rwzi.capaciteit}</div>
                          <div>Havenafstand: {p.nabijheidHavenKm} km</div>
                        </div>
                      </div>
                    </div>
                  );
                })()
              ) : (
                <p className="text-gray-400">Selecteer een agent in de canvas om de data te inspecteren.</p>
              )}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-white/10">
            <button
              className="control-button w-full justify-center text-sm"
              onClick={() => {
                const generatedNetwork = generateSyntheticNetwork();
                onNetworkGenerated(generatedNetwork);
                setGenerationStatus(`${generatedNetwork.nodes.length} agents succesvol gesimuleerd.`);
              }}
            >
              Genereer Netwerk
            </button>
            {generationStatus && <p className="mt-2 text-center text-xs text-gray-400">{generationStatus}</p>}
            
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button className="liquid-glass inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition hover:text-gray-300" onClick={downloadJson}>
                <Download size={14} /> JSON Export
              </button>
              <button className="liquid-glass inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition hover:text-gray-300" onClick={downloadCsv}>
                <Download size={14} /> CSV Export
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}