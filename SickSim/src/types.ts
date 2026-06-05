export type Page = 'Netwerk genereren' | 'Simulatie' | 'Simulatie run';

export type DataFactor = {
  label: string;
  enabled: boolean;
  minFactor: number;
  maxFactor: number;
};

export type AgentProfile = {
  buurtcode: string;
  wijkcode: string;
  bevolkingsomvang: number;
  leeftijd: number;
  huishoudgrootte: number;
  huishoudenSamenstelling: 'Eenpersoon' | 'Koppel' | 'Gezin' | 'Groot gezin';
  aandeelNietWesterseAchtergrond: number;
  woningtype: 'appartement' | 'rijtjeshuis' | 'vrijstaand';
  bezettingsgraadWoning: number;
  gemiddeldBestedbaarInkomen: number;
  stedelijkheidsgraad: number;
  opleidingsniveau: {
    laag: number;
    midden: number;
    hoog: number;
  };
  rwzi: {
    id: string;
    naam: string;
    locatie: string;
    capaciteit: number;
  };
  catchment: {
    oppervlakteKm2: number;
    aansluitingen: number;
  };
  landgebruik: {
    woongebied: number;
    industrie: number;
    agrarisch: number;
  };
  nabijheidHavenKm: number;
};

export type NetworkNode = {
  id: string;
  label?: string;
  x?: number;
  y?: number;
  profile?: AgentProfile;
};

export type NetworkEdge = {
  source: string;
  target: string;
  weight?: number;
};

export type NetworkData = {
  fileName: string;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  warnings: string[];
};

export type NetworkStats = {
  nodeCount: number;
  edgeCount: number;
  meanDegree: number;
  density: number;
  largestDegree: number;
};

export type SimulationConfig = {
  beta: number;
  incubationDays: number;
  infectiousDays: number;
  recoveryChance: number;
  asymptomaticPercentage: number;
  immunityChance: number;
  lethalityChance: number;
};

export type SeirPoint = {
  day: number;
  susceptible: number;
  exposed: number;
  infectious: number;
  recovered: number;
  deaths: number;
};
