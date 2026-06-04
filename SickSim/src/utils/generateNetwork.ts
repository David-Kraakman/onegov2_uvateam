import type { AgentProfile, NetworkData, NetworkEdge, NetworkNode } from '../types';

type GenerateNetworkOptions = {
  nodeCount?: number;
  averageDegree?: number;
};

const buurtcodes = ['BU1180', 'BU1181', 'BU1182', 'BU1183', 'WK0301', 'WK0302'];
const wijkcodes = ['WK0101', 'WK0102', 'WK0103', 'WK0201', 'WK0202'];
const woningtypes = ['appartement', 'rijtjeshuis', 'vrijstaand'] as const;
const huishoudenSamenstellingen = ['Eenpersoon', 'Koppel', 'Gezin', 'Groot gezin'] as const;

export function generateSyntheticNetwork(options: GenerateNetworkOptions = {}): NetworkData {
  const nodeCount = options.nodeCount ?? 160;
  const averageDegree = options.averageDegree ?? randomInteger(5, 11);
  const nodes = createNodes(nodeCount);
  const edges = createEdges(nodes, averageDegree);

  return {
    fileName: `gegenereerd-netwerk-${Date.now()}.json`,
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
      id: `persoon-${index + 1}`,
      label: `Persoon ${index + 1}`,
      x: 300 + centerJitterX + Math.cos(angle) * ring,
      y: 240 + centerJitterY + Math.sin(angle) * ring,
      profile: createAgentProfile(index),
    };
  });
}

function createAgentProfile(index: number): AgentProfile {
  const buurtIndex = index % buurtcodes.length;
  const wijkIndex = index % wijkcodes.length;
  const woonkamerTypeIndex = index % woningtypes.length;
  const huishoudgrootte = randomInteger(1, 5);
  const leeftijdsverdeling = generateAgeDistribution();
  const opleiding = generateEducationDistribution();
  const woningtype = woningtypes[woonkamerTypeIndex];

  return {
    buurtcode: buurtcodes[buurtIndex],
    wijkcode: wijkcodes[wijkIndex],
    bevolkingsomvang: randomInteger(900, 12000),
    leeftijdsverdeling,
    huishoudgrootte,
    huishoudenSamenstelling: huishoudenSamenstellingen[randomInteger(0, huishoudenSamenstellingen.length - 1)],
    aandeelNietWesterseAchtergrond: randomInteger(3, 35),
    woningtype,
    bezettingsgraadWoning: Number((randomNumber(1.2, 2.4)).toFixed(1)),
    gemiddeldBestedbaarInkomen: randomInteger(22000, 72000),
    stedelijkheidsgraad: randomInteger(20, 100),
    opleidingsniveau: opleiding,
    rwzi: {
      id: `RWZI-${100 + index}`,
      naam: `RWZI locatie ${index + 1}`,
      locatie: `Utrecht-${wijkcodes[wijkIndex]}`,
      capaciteit: randomInteger(1500, 8500),
    },
    catchment: {
      oppervlakteKm2: Number(randomNumber(4.2, 22.5).toFixed(1)),
      aansluitingen: randomInteger(4200, 14800),
    },
    landgebruik: {
      woongebied: randomInteger(22, 58),
      industrie: randomInteger(5, 28),
      agrarisch: randomInteger(8, 38),
    },
    nabijheidHavenKm: Number(randomNumber(8, 95).toFixed(1)),
  };
}

function generateAgeDistribution() {
  const distribution = {
    '0-14': randomInteger(8, 20),
    '15-24': randomInteger(8, 18),
    '25-44': randomInteger(22, 34),
    '45-64': randomInteger(20, 30),
    '65+': 0,
  };
  const total = distribution['0-14'] + distribution['15-24'] + distribution['25-44'] + distribution['45-64'];
  distribution['65+'] = 100 - total;
  return distribution;
}

function generateEducationDistribution() {
  const laag = randomInteger(18, 40);
  const midden = randomInteger(22, 46);
  const hoog = Math.max(5, 100 - laag - midden);
  return { laag, midden, hoog };
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
