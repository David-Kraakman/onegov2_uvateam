import type { NetworkData, NetworkEdge, NetworkNode } from '../types';

type RawRecord = Record<string, unknown>;

export async function parseNetworkFile(file: File): Promise<NetworkData> {
  const text = await file.text();
  const extension = file.name.split('.').pop()?.toLowerCase();

  if (extension === 'json' || file.type.includes('json')) {
    return parseJsonNetwork(text, file.name);
  }

  if (extension === 'csv' || file.type.includes('csv')) {
    return parseCsvNetwork(text, file.name);
  }

  throw new Error('Gebruik een JSON- of CSV-bestand voor het netwerk.');
}

function parseJsonNetwork(text: string, fileName: string): NetworkData {
  const raw = JSON.parse(text) as unknown;
  const warnings: string[] = [];
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];

  if (Array.isArray(raw)) {
    edges.push(...recordsToEdges(raw as RawRecord[], warnings));
  } else if (isRecord(raw)) {
    const nodeRecords = Array.isArray(raw.nodes) ? raw.nodes as RawRecord[] : [];
    const edgeRecords = Array.isArray(raw.edges) ? raw.edges as RawRecord[] : [];

    nodes.push(...recordsToNodes(nodeRecords));
    edges.push(...recordsToEdges(edgeRecords, warnings));
  } else {
    throw new Error('JSON-formaat niet herkend. Gebruik { "nodes": [], "edges": [] } of een array met edges.');
  }

  return completeNetwork({ fileName, nodes, edges, warnings });
}

function parseCsvNetwork(text: string, fileName: string): NetworkData {
  const rows = text.trim().split(/\r?\n/).filter(Boolean);
  if (rows.length < 2) throw new Error('CSV bevat geen netwerkregels.');

  const headers = splitCsvLine(rows[0]).map((header) => header.trim().toLowerCase());
  const records = rows.slice(1).map((row) => {
    const values = splitCsvLine(row);
    return Object.fromEntries(headers.map((header, index) => [header, values[index]?.trim() ?? '']));
  });

  const warnings: string[] = [];
  const edges = recordsToEdges(records, warnings);
  return completeNetwork({ fileName, nodes: [], edges, warnings });
}

function recordsToNodes(records: RawRecord[]): NetworkNode[] {
  return records
    .map((record, index) => {
      const id = stringValue(record.id ?? record.name ?? record.label ?? index);
      return {
        id,
        label: stringValue(record.label ?? record.name ?? id),
        x: numberValue(record.x),
        y: numberValue(record.y),
      };
    })
    .filter((node) => node.id);
}

function recordsToEdges(records: RawRecord[], warnings: string[]): NetworkEdge[] {
  return records.flatMap((record) => {
    const source = stringValue(record.source ?? record.from ?? record.src ?? record.Source ?? record.From);
    const target = stringValue(record.target ?? record.to ?? record.dst ?? record.Target ?? record.To);

    if (!source || !target) {
      warnings.push('Een edge is overgeslagen omdat source/target ontbreekt.');
      return [];
    }

    return [{ source, target, weight: numberValue(record.weight) }];
  });
}

function completeNetwork(network: NetworkData): NetworkData {
  const nodeMap = new Map<string, NetworkNode>();

  network.nodes.forEach((node) => nodeMap.set(node.id, node));
  network.edges.forEach((edge) => {
    if (!nodeMap.has(edge.source)) nodeMap.set(edge.source, { id: edge.source });
    if (!nodeMap.has(edge.target)) nodeMap.set(edge.target, { id: edge.target });
  });

  if (nodeMap.size === 0) {
    throw new Error('Geen knopen of verbindingen gevonden in het netwerkbestand.');
  }

  return {
    ...network,
    nodes: Array.from(nodeMap.values()),
  };
}

function splitCsvLine(line: string) {
  return line.match(/("([^"]|"")*"|[^,;]+)/g)?.map((value) => value.replace(/^"|"$/g, '').replace(/""/g, '"')) ?? [];
}

function isRecord(value: unknown): value is RawRecord {
  return typeof value === 'object' && value !== null;
}

function stringValue(value: unknown) {
  return value === undefined || value === null ? '' : String(value).trim();
}

function numberValue(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : undefined;
}
