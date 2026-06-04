import type { NetworkData, NetworkEdge, NetworkNode } from '../types';

type GenerateNetworkOptions = {
  nodeCount?: number;
  averageDegree?: number;
};

export function generateSyntheticNetwork(options: GenerateNetworkOptions = {}): NetworkData {
  const nodeCount = options.nodeCount ?? 160;
  const averageDegree = options.averageDegree ?? randomInteger(5, 11);
  const nodes = createNodes(nodeCount);
  const edges = createEdges(nodes, averageDegree);

  return {
    fileName: `gegenereerd-utrecht-netwerk-${Date.now()}.json`,
    nodes,
    edges,
    warnings: [],
  };
}

function createNodes(nodeCount: number): NetworkNode[] {
  const centerJitterX = randomNumber(-18, 18);
  const centerJitterY = randomNumber(-14, 14);

  return Array.from({ length: nodeCount }, (_, index) => {
    const angle = (index / nodeCount) * Math.PI * 2 + randomNumber(-0.08, 0.08);
    const ring = 90 + (index % 5) * 34 + randomNumber(-18, 18);

    return {
      id: `utrecht-${index + 1}`,
      label: `Utrecht agent ${index + 1}`,
      x: 300 + centerJitterX + Math.cos(angle) * ring,
      y: 240 + centerJitterY + Math.sin(angle) * ring,
    };
  });
}

function createEdges(nodes: NetworkNode[], averageDegree: number): NetworkEdge[] {
  const edges = new Map<string, NetworkEdge>();
  const localConnections = Math.max(2, Math.round(averageDegree * 0.65));
  const randomConnections = Math.max(1, Math.round(averageDegree * 0.18));

  nodes.forEach((node, index) => {
    for (let offset = 1; offset <= localConnections; offset += 1) {
      addEdge(edges, node.id, nodes[(index + offset) % nodes.length].id, 1);
    }

    if (index % 4 === 0) {
      const householdTarget = nodes[(index + 1) % nodes.length];
      addEdge(edges, node.id, householdTarget.id, 1.6);
    }

    for (let jump = 0; jump < randomConnections; jump += 1) {
      const targetIndex = randomInteger(0, nodes.length - 1);
      addEdge(edges, node.id, nodes[targetIndex].id, randomNumber(0.4, 1.2));
    }
  });

  return Array.from(edges.values());
}

function addEdge(edges: Map<string, NetworkEdge>, source: string, target: string, weight: number) {
  if (source === target) return;

  const [a, b] = source < target ? [source, target] : [target, source];
  const key = `${a}-${b}`;
  if (!edges.has(key)) {
    edges.set(key, { source: a, target: b, weight });
  }
}

function randomInteger(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomNumber(min: number, max: number) {
  return Math.random() * (max - min) + min;
}
