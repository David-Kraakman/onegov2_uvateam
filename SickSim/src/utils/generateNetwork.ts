import type { AgentProfile, NetworkData, NetworkEdge, NetworkNode } from '../types';

type GenerateNetworkOptions = {
  nodeCount?: number;
  averageDegree?: number;
};

const buurtcodes = ['BU1180', 'BU1181', 'BU1182', 'BU1183'];
const wijkcodes = ['WK0301', 'WK0302'];
const woningtypes = ['appartement', 'rijtjeshuis', 'vrijstaand'] as const;
const huishoudenSamenstellingen = ['Eenpersoon', 'Koppel', 'Gezin', 'Groot gezin'] as const;

// We geven elke buurt een fysieke locatie op de 'kaart'
const buurtCenters: Record<string, { x: number; y: number }> = {
  'BU1180': { x: 200, y: 200 },
  'BU1181': { x: 600, y: 200 },
  'BU1182': { x: 200, y: 600 },
  'BU1183': { x: 600, y: 600 },
};

export function generateSyntheticNetwork(options: GenerateNetworkOptions = {}): NetworkData {
  const nodeCount = options.nodeCount ?? 400; // Verhoogd naar 400 voor een drukker netwerk
  const averageDegree = options.averageDegree ?? randomInteger(4, 9);
  const nodes = createNodes(nodeCount);
  const edges = createEdges(nodes, averageDegree);

  return {
    fileName: `abm-netwerk-${Date.now()}.json`,
    nodes,
    edges,
    warnings: [],
  };
}

function createNodes(nodeCount: number): NetworkNode[] {
  return Array.from({ length: nodeCount }, (_, index) => {
    const buurtIndex = index % buurtcodes.length;
    const buurtcode = buurtcodes[buurtIndex];
    
    // Haal het middelpunt van deze specifieke buurt op
    const center = buurtCenters[buurtcode];
    
    // Verspreid de inwoners rondom het middelpunt van hun eigen buurt
    const radius = randomNumber(10, 160); // Hoe groot is de wijk visueel
    const angle = randomNumber(0, Math.PI * 2);

    return {
      id: `persoon-${index + 1}`,
      label: `Agent ${index + 1}`,
      x: center.x + Math.cos(angle) * radius,
      y: center.y + Math.sin(angle) * radius,
      profile: createAgentProfile(index, buurtcode, wijkcodes[index % wijkcodes.length]),
    };
  });
}

function createAgentProfile(index: number, buurtcode: string, wijkcode: string): AgentProfile {
  const woningTypeIndex = index % woningtypes.length;

  const l_0_14 = randomInteger(10, 22);
  const l_15_24 = randomInteger(8, 18);
  const l_25_44 = randomInteger(22, 35);
  const l_45_64 = randomInteger(20, 30);
  const l_65_plus = 100 - (l_0_14 + l_15_24 + l_25_44 + l_45_64);

  const o_laag = randomInteger(15, 35);
  const o_midden = randomInteger(30, 50);
  const o_hoog = 100 - (o_laag + o_midden);

  const bezettingsgraadWoning = Number(randomNumber(1.2, 3.6).toFixed(1));

  return {
    buurtcode, // Direct gekoppeld aan de fysieke cluster!
    wijkcode,
    bevolkingsomvang: randomInteger(800, 14000),
    leeftijdsverdeling: { '0-14': l_0_14, '15-24': l_15_24, '25-44': l_25_44, '45-64': l_45_64, '65+': l_65_plus },
    huishoudgrootte: bezettingsgraadWoning,
    huishoudenSamenstelling: huishoudenSamenstellingen[randomInteger(0, huishoudenSamenstellingen.length - 1)],
    aandeelNietWesterseAchtergrond: randomInteger(3, 45),
    woningtype: woningtypes[woningTypeIndex],
    bezettingsgraadWoning,
    gemiddeldBestedbaarInkomen: randomInteger(24000, 68000),
    stedelijkheidsgraad: randomInteger(1, 5),
    opleidingsniveau: { laag: o_laag, midden: o_midden, hoog: o_hoog },
    rwzi: { id: `RWZI-${100 + index}`, naam: `RWZI Locatie ${index + 1}`, locatie: `Utrecht-${wijkcode}`, capaciteit: randomInteger(2000, 9500) },
    catchment: { oppervlakteKm2: Number(randomNumber(4.0, 20.0).toFixed(1)), aansluitingen: randomInteger(3500, 14000) },
    landgebruik: { woongebied: randomInteger(25, 60), industrie: randomInteger(5, 25), agrarisch: randomInteger(0, 30) },
    nabijheidHavenKm: Number(randomNumber(3.5, 65.0).toFixed(1)),
  };
}

function createEdges(nodes: NetworkNode[], averageDegree: number): NetworkEdge[] {
  const edges = new Map<string, NetworkEdge>();
  
  // Connecties worden nu logischer: veel contact binnen de eigen buurt, minder daarbuiten
  nodes.forEach((node, index) => {
    // Zoek mensen in DEZELFDE buurt voor sterke lokale connecties
    const buren = nodes.filter(n => n.profile?.buurtcode === node.profile?.buurtcode && n.id !== node.id);
    const localConnections = Math.max(2, Math.round(averageDegree * 0.7));
    
    for (let i = 0; i < localConnections; i++) {
      if (buren.length > 0) {
        const buur = buren[randomInteger(0, buren.length - 1)];
        addEdge(edges, node.id, buur.id, 1);
      }
    }

    // Willekeurige connecties naar andere wijken (werk/school/sport)
    const randomConnections = Math.max(1, Math.round(averageDegree * 0.3));
    for (let jump = 0; jump < randomConnections; jump += 1) {
      const targetIndex = randomInteger(0, nodes.length - 1);
      addEdge(edges, node.id, nodes[targetIndex].id, 0.5);
    }
  });

  return Array.from(edges.values());
}

function addEdge(edges: Map<string, NetworkEdge>, source: string, target: string, weight: number) {
  if (source === target) return;
  const [a, b] = source < target ? [source, target] : [target, source];
  const key = `${a}-${b}`;
  if (!edges.has(key)) edges.set(key, { source: a, target: b, weight });
}

function randomInteger(min: number, max: number) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function randomNumber(min: number, max: number) { return Math.random() * (max - min) + min; }