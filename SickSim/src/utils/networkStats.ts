import type { DataFactor, NetworkData, NetworkStats, SeirPoint, SimulationConfig } from '../types';

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

export function runNetworkSeir(network: NetworkData | null, config: SimulationConfig, dataFactors: DataFactor[]): SeirPoint[] {
  const stats = getNetworkStats(network);
  const population = Math.max(stats.nodeCount, 1);
  const averageContacts = Math.max(stats.meanDegree, 1);
  const factorMultiplier = calculateFactorMultiplier(network, dataFactors);
  const transmissionRate = Math.min(0.95, config.beta * averageContacts * 0.12 * factorMultiplier);
  const incubationRate = 1 / Math.max(config.incubationDays, 1);
  const recoveryRate = Math.max(config.recoveryChance, 1 / Math.max(config.infectiousDays, 1));

  let susceptible = Math.max(population - 1, 0);
  let exposed = 0;
  let infectious = 1;
  let recovered = 0;
  const points: SeirPoint[] = [];
  const maxDays = 120;

  let exposedRemainder = 0;
  let infectiousRemainder = 0;
  let recoveredRemainder = 0;

  let terminatedEarly = false;

  for (let day = 0; day < maxDays; day += 1) {
    const rawNewExposed = transmissionRate * infectious * susceptible / population + exposedRemainder;
    const rawNewInfectious = exposed * incubationRate + infectiousRemainder;
    const rawNewRecovered = infectious * recoveryRate + recoveredRemainder;

    const newExposed = Math.min(susceptible, Math.max(0, Math.floor(rawNewExposed)));
    const newInfectious = Math.min(exposed, Math.max(0, Math.floor(rawNewInfectious)));
    const newRecovered = Math.min(infectious, Math.max(0, Math.floor(rawNewRecovered)));

    exposedRemainder = rawNewExposed - newExposed;
    infectiousRemainder = rawNewInfectious - newInfectious;
    recoveredRemainder = rawNewRecovered - newRecovered;

    points.push({
      day,
      susceptible,
      exposed,
      infectious,
      recovered,
    });

    let nextSusceptible = susceptible - newExposed;
    let nextExposed = exposed + newExposed - newInfectious;
    let nextInfectious = infectious + newInfectious - newRecovered;
    let nextRecovered = recovered + newRecovered;

    const total = nextSusceptible + nextExposed + nextInfectious + nextRecovered;
    const diff = population - total;

    if (diff !== 0) {
      if (diff > 0) {
        nextSusceptible += diff;
      } else {
        let remaining = -diff;
        const subtractFrom = [() => Math.min(nextRecovered, remaining), () => Math.min(nextInfectious, remaining), () => Math.min(nextExposed, remaining), () => Math.min(nextSusceptible, remaining)];
        const update = [
          (value: number) => { nextRecovered -= value; remaining -= value; },
          (value: number) => { nextInfectious -= value; remaining -= value; },
          (value: number) => { nextExposed -= value; remaining -= value; },
          (value: number) => { nextSusceptible -= value; remaining -= value; },
        ];

        for (let i = 0; i < subtractFrom.length && remaining > 0; i += 1) {
          const amount = subtractFrom[i]();
          update[i](amount);
        }
      }
    }

    susceptible = Math.max(0, Math.round(nextSusceptible));
    exposed = Math.max(0, Math.round(nextExposed));
    infectious = Math.max(0, Math.round(nextInfectious));
    recovered = Math.max(0, Math.round(nextRecovered));

    if (day >= 20 && exposed + infectious < 1) {
      terminatedEarly = true;
      break;
    }
  }

  if (terminatedEarly) {
    const lastPoint = points[points.length - 1];
    points.push({
      day: lastPoint.day + 1,
      susceptible,
      exposed,
      infectious,
      recovered,
    });
  }

  return points;
}

function calculateFactorMultiplier(network: NetworkData | null, dataFactors: DataFactor[]): number {
  const activeFactors = dataFactors.filter((factor) => factor.enabled && factor.weight > 0);
  if (!network || activeFactors.length === 0) {
    return 1;
  }

  const profiles = network.nodes
    .map((node) => node.profile)
    .filter((profile): profile is NonNullable<NetworkData['nodes'][number]['profile']> => Boolean(profile));

  if (profiles.length === 0) {
    return 1;
  }

  const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));
  const normalize = (value: number, min: number, max: number) => (min === max ? 0 : clamp((value - min) / (max - min), 0, 1));
  const average = (values: number[]) => (values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length);

  const uniqueAreaCount = new Set(profiles.map((profile) => `${profile.buurtcode}-${profile.wijkcode}`)).size;
  const averagePopulation = average(profiles.map((profile) => profile.bevolkingsomvang));
  const averageHouseholdSize = average(profiles.map((profile) => profile.huishoudgrootte));
  const averageNonWestern = average(profiles.map((profile) => profile.aandeelNietWesterseAchtergrond));
  const averageApartmentShare = average(profiles.map((profile) => (profile.woningtype === 'appartement' ? 1 : 0)));
  const averageOccupancy = average(profiles.map((profile) => profile.bezettingsgraadWoning));
  const averageIncome = average(profiles.map((profile) => profile.gemiddeldBestedbaarInkomen));
  const averageUrbanity = average(profiles.map((profile) => profile.stedelijkheidsgraad));
  const averageLowEducation = average(profiles.map((profile) => profile.opleidingsniveau.laag));
  const averageRwziCapacity = average(profiles.map((profile) => profile.rwzi.capaciteit));
  const averageCatchment = average(profiles.map((profile) => profile.catchment.aansluitingen));
  const averageLandWoon = average(profiles.map((profile) => profile.landgebruik.woongebied));
  const averageLandIndustry = average(profiles.map((profile) => profile.landgebruik.industrie));
  const averageLandAgrarisch = average(profiles.map((profile) => profile.landgebruik.agrarisch));
  const averagePortProximity = average(profiles.map((profile) => profile.nabijheidHavenKm));
  const averageYoungOld = average(profiles.map((profile) => profile.leeftijdsverdeling['0-14'] + profile.leeftijdsverdeling['65+']));

  const factorEffects = activeFactors.map((factor) => {
    const weight = Math.max(0, factor.weight);
    if (factor.label.includes('Buurtcode / wijkcode')) {
      return 1 + 0.05 * weight * normalize(uniqueAreaCount, 2, 15);
    }
    if (factor.label.includes('Bevolkingsomvang')) {
      return 1 + 0.05 * weight * normalize(averagePopulation, 1000, 12000);
    }
    if (factor.label.includes('Leeftijdsverdeling')) {
      return 1 + 0.04 * weight * normalize(averageYoungOld, 15, 45);
    }
    if (factor.label.includes('Huishoudgrootte')) {
      return 1 + 0.05 * weight * normalize(averageHouseholdSize, 1.2, 3.1);
    }
    if (factor.label.includes('aandeel niet-westerse')) {
      return 1 + 0.04 * weight * normalize(averageNonWestern, 5, 40);
    }
    if (factor.label.includes('Woningtype')) {
      return 1 + 0.05 * weight * averageApartmentShare;
    }
    if (factor.label.includes('Bezettingsgraad')) {
      return 1 + 0.05 * weight * normalize(averageOccupancy, 1.1, 2.4);
    }
    if (factor.label.includes('Inkomen')) {
      return 1 + 0.04 * weight * (1 - normalize(averageIncome, 22000, 72000));
    }
    if (factor.label.includes('Stedelijkheidsgraad')) {
      return 1 + 0.06 * weight * normalize(averageUrbanity, 20, 100);
    }
    if (factor.label.includes('Opleidingsniveau')) {
      return 1 + 0.05 * weight * normalize(averageLowEducation, 0.18, 0.42);
    }
    if (factor.label.includes('RWZI')) {
      return 1 + 0.03 * weight * normalize(averageRwziCapacity, 1500, 8500);
    }
    if (factor.label.includes('Catchment')) {
      return 1 + 0.03 * weight * normalize(averageCatchment, 4, 24);
    }
    if (factor.label.includes('woongebied')) {
      return 1 + 0.03 * weight * normalize(averageLandWoon, 20, 65);
    }
    if (factor.label.includes('industrie')) {
      return 1 + 0.03 * weight * normalize(averageLandIndustry, 5, 30);
    }
    if (factor.label.includes('agrarisch')) {
      return 1 - 0.02 * weight * normalize(averageLandAgrarisch, 8, 38);
    }
    if (factor.label.includes('haven')) {
      return 1 + 0.03 * weight * (1 - normalize(averagePortProximity, 8, 95));
    }
    return 1;
  });

  const multiplier = factorEffects.reduce((acc, effect) => acc * effect, 1);
  return clamp(multiplier, 0.6, 1.5);
}
