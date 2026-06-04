import type { NetworkData, NetworkStats, SeirPoint, SimulationConfig } from '../types';

export function getNetworkStats(network: NetworkData | null): NetworkStats {
  if (!network) {
    return { nodeCount: 1248, edgeCount: 7931, meanDegree: 12.7, density: 0.01, largestDegree: 24 };
  }

  const degree = new Map<string, number>();
  network.nodes.forEach((node) => degree.set(node.id, 0));
  network.edges.forEach((edge) => {
    degree.set(edge.source, (degree.get(edge.source) ?? 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) ?? 0) + 1);
  });

  const nodeCount = network.nodes.length;
  const edgeCount = network.edges.length;
  const possibleEdges = nodeCount * Math.max(nodeCount - 1, 1) / 2;
  const degreeValues = Array.from(degree.values());

  return {
    nodeCount,
    edgeCount,
    meanDegree: nodeCount > 0 ? (edgeCount * 2) / nodeCount : 0,
    density: possibleEdges > 0 ? edgeCount / possibleEdges : 0,
    largestDegree: Math.max(0, ...degreeValues),
  };
}

export function runNetworkSeir(network: NetworkData | null, config: SimulationConfig): SeirPoint[] {
  const stats = getNetworkStats(network);
  const population = Math.max(stats.nodeCount, 1);
  const averageContacts = Math.max(stats.meanDegree, 1);
  const transmissionRate = Math.min(0.95, config.beta * averageContacts * 0.12);
  const incubationRate = 1 / Math.max(config.incubationDays, 1);
  const recoveryRate = Math.max(config.recoveryChance, 1 / Math.max(config.infectiousDays, 1));

  let susceptible = Math.max(population - 1, 0);
  let exposed = 0;
  let infectious = 1;
  let recovered = 0;

  return Array.from({ length: 42 }, (_, day) => {
    const newExposed = Math.min(susceptible, transmissionRate * infectious * susceptible / population);
    const newInfectious = Math.min(exposed, exposed * incubationRate);
    const newRecovered = Math.min(infectious, infectious * recoveryRate);

    const point = {
      day,
      susceptible,
      exposed,
      infectious,
      recovered,
    };

    susceptible -= newExposed;
    exposed += newExposed - newInfectious;
    infectious += newInfectious - newRecovered;
    recovered += newRecovered;

    return point;
  });
}
