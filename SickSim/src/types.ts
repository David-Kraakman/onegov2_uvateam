export type Page = 'Pipeline overzicht' | 'Netwerk genereren' | 'Simulatie' | 'Simulatie run';

export type DataFactor = {
  label: string;
  enabled: boolean;
  weight: number;
};

export type NetworkNode = {
  id: string;
  label?: string;
  x?: number;
  y?: number;
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
};

export type SeirPoint = {
  day: number;
  susceptible: number;
  exposed: number;
  infectious: number;
  recovered: number;
};
