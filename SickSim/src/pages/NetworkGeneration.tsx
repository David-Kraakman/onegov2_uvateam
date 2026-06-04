import React from 'react';
import { BarChart3, Download } from 'lucide-react';
import { NetworkCanvas } from '../components/NetworkCanvas';
import type { NetworkData } from '../types';
import { generateSyntheticNetwork } from '../utils/generateNetwork';
import { getNetworkStats } from '../utils/networkStats';

type NetworkGenerationProps = {
  network: NetworkData | null;
  onNetworkGenerated: (network: NetworkData) => void;
};

export function NetworkGeneration({ network, onNetworkGenerated }: NetworkGenerationProps) {
  const [generationStatus, setGenerationStatus] = React.useState('');
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);
  const stats = getNetworkStats(network);
  const rows = [
    ['Bron', network?.fileName ?? 'Demo-netwerk'],
    ['Knopen', stats.nodeCount.toLocaleString('nl-NL')],
    ['Verbindingen', stats.edgeCount.toLocaleString('nl-NL')],
    ['Gemiddelde graad', stats.meanDegree.toLocaleString('nl-NL', { maximumFractionDigits: 2 })],
    ['Dichtheid', stats.density.toLocaleString('nl-NL', { maximumFractionDigits: 4 })],
    ['Hoogste graad', stats.largestDegree.toLocaleString('nl-NL')],
  ];
  const downloadJson = () => {
    if (!network) {
      setGenerationStatus('Genereer of upload eerst een netwerk voordat je downloadt.');
      return;
    }

    const content = JSON.stringify({ nodes: network.nodes, edges: network.edges }, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    let name = network.fileName;
    if (name.endsWith('.csv')) {
      name = name.slice(0, -4) + '.json';
    } else if (!name.endsWith('.json')) {
      name = `${name}.json`;
    }

    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
    setGenerationStatus(`${name} is gedownload.`);
  };

  const escapeCsvValue = (value: string | number | undefined | null) => {
    if (value === undefined || value === null) return '';
    const stringValue = String(value);
    const escaped = stringValue.replace(/"/g, '""');
    return `"${escaped}"`;
  };

  const downloadCsv = () => {
    if (!network) {
      setGenerationStatus('Genereer of upload eerst een netwerk voordat je downloadt.');
      return;
    }

    const headers = [
      'id',
      'label',
      'buurtcode',
      'wijkcode',
      'bevolkingsomvang',
      'huishoudgrootte',
      'huishoudenSamenstelling',
      'aandeelNietWesterseAchtergrond',
      'woningtype',
      'bezettingsgraadWoning',
      'gemiddeldBestedbaarInkomen',
      'stedelijkheidsgraad',
      'leeftijd_0_14',
      'leeftijd_15_24',
      'leeftijd_25_44',
      'leeftijd_45_64',
      'leeftijd_65_plus',
      'opleidingsniveau_laag',
      'opleidingsniveau_midden',
      'opleidingsniveau_hoog',
      'rwzi_id',
      'rwzi_naam',
      'rwzi_locatie',
      'rwzi_capaciteit',
      'catchment_oppervlakteKm2',
      'catchment_aansluitingen',
      'landgebruik_woongebied',
      'landgebruik_industrie',
      'landgebruik_agrarisch',
      'nabijheidHavenKm',
    ];

    const csvRows = [headers.join(',')];

    network.nodes.forEach((node) => {
      const profile = node.profile;
      csvRows.push([
        escapeCsvValue(node.id),
        escapeCsvValue(node.label),
        escapeCsvValue(profile?.buurtcode),
        escapeCsvValue(profile?.wijkcode),
        escapeCsvValue(profile?.bevolkingsomvang),
        escapeCsvValue(profile?.huishoudgrootte),
        escapeCsvValue(profile?.huishoudenSamenstelling),
        escapeCsvValue(profile?.aandeelNietWesterseAchtergrond),
        escapeCsvValue(profile?.woningtype),
        escapeCsvValue(profile?.bezettingsgraadWoning),
        escapeCsvValue(profile?.gemiddeldBestedbaarInkomen),
        escapeCsvValue(profile?.stedelijkheidsgraad),
        escapeCsvValue(profile?.leeftijdsverdeling['0-14']),
        escapeCsvValue(profile?.leeftijdsverdeling['15-24']),
        escapeCsvValue(profile?.leeftijdsverdeling['25-44']),
        escapeCsvValue(profile?.leeftijdsverdeling['45-64']),
        escapeCsvValue(profile?.leeftijdsverdeling['65+']),
        escapeCsvValue(profile?.opleidingsniveau?.laag),
        escapeCsvValue(profile?.opleidingsniveau?.midden),
        escapeCsvValue(profile?.opleidingsniveau?.hoog),
        escapeCsvValue(profile?.rwzi?.id),
        escapeCsvValue(profile?.rwzi?.naam),
        escapeCsvValue(profile?.rwzi?.locatie),
        escapeCsvValue(profile?.rwzi?.capaciteit),
        escapeCsvValue(profile?.catchment?.oppervlakteKm2),
        escapeCsvValue(profile?.catchment?.aansluitingen),
        escapeCsvValue(profile?.landgebruik?.woongebied),
        escapeCsvValue(profile?.landgebruik?.industrie),
        escapeCsvValue(profile?.landgebruik?.agrarisch),
        escapeCsvValue(profile?.nabijheidHavenKm),
      ].join(','));
    });

    const content = csvRows.join('\n');
    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let name = network.fileName;
    if (name.endsWith('.json')) {
      name = name.slice(0, -5) + '.csv';
    } else if (!name.endsWith('.csv')) {
      name = `${name}.csv`;
    }

    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
    setGenerationStatus(`${name} is gedownload.`);
  };

  React.useEffect(() => {
    setSelectedNodeId(null);
  }, [network]);

  return (
    <div className="mx-auto grid w-full max-w-6xl items-stretch gap-6 py-8 lg:grid-cols-[1fr_320px]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10 h-full">
          <h1 className="mb-4 text-3xl font-normal tracking-tight">Netwerk genereren</h1>
          <NetworkCanvas network={network} selectedNodeId={selectedNodeId ?? undefined} onNodeSelect={setSelectedNodeId} />
          <p className="mt-4 text-sm text-gray-300">Klik op een agent in het netwerk om diens eigenschappen te bekijken.</p>
        </div>
      </div>
      <aside className="liquid-glass rounded-2xl p-6 h-full">
        <div className="relative z-10 flex h-full flex-col">
          <div className="custom-scrollbar flex-1 overflow-y-auto pr-2">
            <div className="relative z-10">
              <h2 className="mb-5 flex items-center gap-2 text-lg font-medium"><BarChart3 size={18} /> Netwerkstatistieken</h2>
              {rows.map(([label, value]) => (
                <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3 text-sm" key={label}>
                  <span className="text-gray-300">{label}</span>
                  <span className="max-w-[150px] truncate text-right font-medium">{value}</span>
                </div>
              ))}
              <div className="mt-6 rounded-2xl border border-white/10 bg-black/25 p-4 text-sm text-gray-300">
                <h3 className="mb-3 text-base font-semibold">Geselecteerde agent</h3>
                {network && selectedNodeId ? (
                  (() => {
                    const node = network.nodes.find((item) => item.id === selectedNodeId);
                    if (!node?.profile) return <p>Deze agent heeft nog geen profiel.</p>;

                    return (
                      <div className="space-y-3">
                        <div className="rounded-xl border border-white/10 bg-black/20 p-3">
                          <div className="text-sm font-medium text-white">{node.label}</div>
                          <div className="text-xs text-gray-400">{node.profile.buurtcode} / {node.profile.wijkcode}</div>
                        </div>
                        <div className="grid gap-2">
                          <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                            <div className="text-xs uppercase tracking-[0.14em] text-gray-400">Demografie</div>
                            <div className="mt-2 text-sm text-gray-200"><strong>Bevolking:</strong> {node.profile.bevolkingsomvang}</div>
                            <div className="text-sm text-gray-200"><strong>Huishoudgrootte:</strong> {node.profile.huishoudgrootte}</div>
                            <div className="text-sm text-gray-200"><strong>Huishouden:</strong> {node.profile.huishoudenSamenstelling}</div>
                          </div>
                          <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                            <div className="text-xs uppercase tracking-[0.14em] text-gray-400">Wonen</div>
                            <div className="mt-2 text-sm text-gray-200"><strong>Woningtype:</strong> {node.profile.woningtype}</div>
                            <div className="text-sm text-gray-200"><strong>Bezettingsgraad:</strong> {node.profile.bezettingsgraadWoning}</div>
                          </div>
                          <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                            <div className="text-xs uppercase tracking-[0.14em] text-gray-400">Sociaal</div>
                            <div className="mt-2 text-sm text-gray-200"><strong>Inkomen:</strong> €{node.profile.gemiddeldBestedbaarInkomen.toLocaleString('nl-NL')}</div>
                            <div className="text-sm text-gray-200"><strong>Niet-westers aandeel:</strong> {node.profile.aandeelNietWesterseAchtergrond}%</div>
                          </div>
                          <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                            <div className="text-xs uppercase tracking-[0.14em] text-gray-400">Meta</div>
                            <div className="mt-2 text-sm text-gray-200"><strong>RWZI:</strong> {node.profile.rwzi.id} ({node.profile.rwzi.capaciteit})</div>
                            <div className="text-sm text-gray-200"><strong>Catchment:</strong> {node.profile.catchment.oppervlakteKm2} km²</div>
                            <div className="text-sm text-gray-200"><strong>Nabijheid haven:</strong> {node.profile.nabijheidHavenKm} km</div>
                          </div>
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <p>Genereer eerst een netwerk en klik daarna op een agent.</p>
                )}
              </div>
            </div>
          </div>
          <div className="mt-4">
            <button
              className="control-button mt-4 w-full justify-center"
              onClick={() => {
                const generatedNetwork = generateSyntheticNetwork();
                onNetworkGenerated(generatedNetwork);
                setGenerationStatus(`${generatedNetwork.nodes.length} knopen en ${generatedNetwork.edges.length} verbindingen gegenereerd`);
              }}
            >
              Genereer netwerk
            </button>
            {generationStatus && <p className="mt-3 text-xs leading-5 text-gray-300">{generationStatus}</p>}
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button className="liquid-glass inline-flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition hover:text-gray-300" onClick={downloadJson}>
                <Download size={16} /> JSON
              </button>
              <button className="liquid-glass inline-flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition hover:text-gray-300" onClick={downloadCsv}>
                <Download size={16} /> CSV
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
