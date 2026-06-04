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

  const downloadCsv = () => {
    if (!network) {
      setGenerationStatus('Genereer of upload eerst een netwerk voordat je downloadt.');
      return;
    }

    const csvRows = ['source,target,weight'];
    network.edges.forEach((edge) => {
      const weight = edge.weight !== undefined ? edge.weight : 1;
      csvRows.push(`${edge.source},${edge.target},${weight}`);
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
          <div className="mt-4 grid grid-cols-2 gap-2">
            <button className="liquid-glass inline-flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition hover:text-gray-300" onClick={downloadJson}>
              <Download size={16} /> JSON
            </button>
            <button className="liquid-glass inline-flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition hover:text-gray-300" onClick={downloadCsv}>
              <Download size={16} /> CSV
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
}
