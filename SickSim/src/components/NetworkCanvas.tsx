import type { NetworkData } from '../types';

type PositionedNode = {
  id: string;
  x: number;
  y: number;
};

type NetworkCanvasProps = {
  network: NetworkData | null;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string) => void;
};

export function NetworkCanvas({ network, selectedNodeId, onNodeSelect }: NetworkCanvasProps) {
  const nodes: PositionedNode[] = network ? network.nodes.map((node, i) => {
    const angle = (i / Math.max(network.nodes.length, 1)) * Math.PI * 2;
    const ring = 110 + (i % 4) * 38;
    return {
      id: node.id,
      x: typeof node.x === 'number' ? node.x : 300 + Math.cos(angle) * ring,
      y: typeof node.y === 'number' ? node.y : 240 + Math.sin(angle) * ring,
    };
  }) : Array.from({ length: 22 }, (_, i) => {
    const angle = (i / 22) * Math.PI * 2;
    const radius = i % 3 === 0 ? 185 : 120 + (i % 5) * 12;
    return { id: String(i), x: 300 + Math.cos(angle) * radius, y: 240 + Math.sin(angle) * radius };
  });
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const edges = network?.edges.slice(0, 650) ?? nodes.flatMap((node, i) => nodes.slice(i + 1, i + 4).map((target) => ({ source: node.id, target: target.id })));

  return (
    <svg viewBox="0 0 600 480" className="h-[480px] w-full rounded-lg border border-white/10 bg-black/30">
      {edges.map((edge, index) => {
        const source = nodeById.get(edge.source);
        const target = nodeById.get(edge.target);
        if (!source || !target) return null;
        return <line key={`${edge.source}-${edge.target}-${index}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="rgba(255,255,255,0.2)" strokeWidth="1" />;
      })}
      {nodes.map((node, i) => {
        const selected = node.id === selectedNodeId;
        return (
          <circle
            key={node.id}
            cx={node.x}
            cy={node.y}
            r={selected ? 9 : i % 4 === 0 ? 8 : 5}
            fill="white"
            stroke={selected ? 'rgba(255,255,255,0.95)' : 'transparent'}
            strokeWidth={selected ? 2 : 0}
            opacity={selected ? 1 : i % 4 === 0 ? 0.95 : 0.65}
            style={{ cursor: onNodeSelect ? 'pointer' : 'default' }}
            onClick={() => onNodeSelect?.(node.id)}
          />
        );
      })}
      {network && <text x="20" y="34" fill="rgba(255,255,255,0.72)" fontSize="13">{network.nodes.length} knopen, {network.edges.length} verbindingen</text>}
    </svg>
  );
}
