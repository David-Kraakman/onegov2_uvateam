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
  const stats = getNetworkStats(network);
  const rows = [
    ['Bron', network?.fileName ?? 'Demo-netwerk'],
    ['Knopen', stats.nodeCount.toLocaleString('nl-NL')],
    ['Verbindingen', stats.edgeCount.toLocaleString('nl-NL')],
    ['Gemiddelde graad', stats.meanDegree.toLocaleString('nl-NL', { maximumFractionDigits: 2 })],
    ['Dichtheid', stats.density.toLocaleString('nl-NL', { maximumFractionDigits: 4 })],
    ['Hoogste graad', stats.largestDegree.toLocaleString('nl-NL')],
  ];
  const downloadNetwork = () => {
    if (!network) {
      setGenerationStatus('Genereer of upload eerst een netwerk voordat je downloadt.');
      return;
    }

    const content = JSON.stringify({ nodes: network.nodes, edges: network.edges }, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = network.fileName.endsWith('.json') ? network.fileName : `${network.fileName}.json`;
    link.click();
    URL.revokeObjectURL(url);
    setGenerationStatus(`${network.fileName} is gedownload.`);
  };

  return (
    <div className="mx-auto grid w-full max-w-6xl items-center gap-6 py-8 lg:grid-cols-[1fr_320px]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10 h-full">
          <h1 className="mb-4 text-3xl font-normal tracking-tight">Netwerk genereren</h1>
          <NetworkCanvas network={network} />
        </div>
      </div>
      <aside className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h2 className="mb-5 flex items-center gap-2 text-lg font-medium"><BarChart3 size={18} /> Netwerkstatistieken</h2>
          {rows.map(([label, value]) => (
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3 text-sm" key={label}>
              <span className="text-gray-300">{label}</span>
              <span className="max-w-[150px] truncate text-right font-medium">{value}</span>
            </div>
          ))}
          <button
            className="control-button mt-2 w-full justify-center"
            onClick={() => {
              const generatedNetwork = generateSyntheticNetwork();
              onNetworkGenerated(generatedNetwork);
              setGenerationStatus(`${generatedNetwork.nodes.length} knopen en ${generatedNetwork.edges.length} verbindingen gegenereerd`);
            }}
          >
            Genereer netwerk
          </button>
          {generationStatus && <p className="mt-3 text-xs leading-5 text-gray-300">{generationStatus}</p>}
          <button className="liquid-glass mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-medium transition hover:text-gray-300" onClick={downloadNetwork}>
            <Download size={16} /> Download netwerk (JSON/CSV)
          </button>
        </div>
      </aside>
    </div>
  );
}
