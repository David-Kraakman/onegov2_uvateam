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

function randomBinomial(trials: number, probability: number): number {
  if (trials <= 0 || probability <= 0) {
    return 0;
  }
  if (probability >= 1) {
    return trials;
  }

  let successes = 0;
  for (let i = 0; i < trials; i += 1) {
    if (Math.random() < probability) {
      successes += 1;
    }
  }

  return successes;
}

export function runNetworkSeir(network: NetworkData | null, config: SimulationConfig, dataFactors: DataFactor[]): SeirPoint[] {
  const stats = getNetworkStats(network);
  const population = Math.max(stats.nodeCount, 1);
  const averageContacts = Math.max(stats.meanDegree, 1);
  const factorMultiplier = calculateFactorMultiplier(network, dataFactors);
  const asymptomaticFraction = Math.max(0, Math.min(100, config.asymptomaticPercentage)) / 100;
  const asymptomaticMultiplier = 1 + asymptomaticFraction * 0.5;
  const transmissionRate = Math.min(0.95, (config.beta / 100) * averageContacts * 0.12 * factorMultiplier * asymptomaticMultiplier);
  const incubationRate = 1 / Math.max(config.incubationDays, 1);
  const infectiousDuration = Math.max(config.infectiousDays, 1);
  const recoveryRateFromDuration = 1 / infectiousDuration;
  const recoveryRate = Math.max(0, Math.min(1, ((config.recoveryChance / 100) + recoveryRateFromDuration) / 2));
  const immunityFraction = Math.max(0, Math.min(100, config.immunityChance)) / 100;
  const lethalityFraction = Math.max(0, Math.min(100, config.lethalityChance)) / 100;

  let susceptible = Math.max(population - 1, 0);
  let exposed = 0;
  let infectious = 1;
  let recovered = 0;
  let deaths = 0;
  const points: SeirPoint[] = [];
  const maxDays = 360;
  let day = 0;

  while (day < maxDays) {
    points.push({
      day,
      susceptible,
      exposed,
      infectious,
      recovered,
      deaths,
    });

    const alivePopulation = Math.max(susceptible + exposed + infectious + recovered, 1);
    const infectionProbability = Math.min(1, transmissionRate * infectious / alivePopulation);
    const newExposed = randomBinomial(susceptible, infectionProbability);
    const newInfectious = randomBinomial(exposed, incubationRate);
    const newRecovered = randomBinomial(infectious, recoveryRate);
    const deathCount = randomBinomial(newRecovered, lethalityFraction);
    const survivors = newRecovered - deathCount;
    const immuneRecoveries = randomBinomial(survivors, immunityFraction);
    const recoveredToSusceptible = survivors - immuneRecoveries;

    const nextSusceptible = Math.max(0, susceptible - newExposed + recoveredToSusceptible);
    const nextExposed = Math.max(0, exposed + newExposed - newInfectious);
    const nextInfectious = Math.max(0, infectious + newInfectious - newRecovered);
    const nextRecovered = Math.max(0, recovered + immuneRecoveries);
    const nextDeaths = Math.max(0, deaths + deathCount);

    if (nextExposed + nextInfectious === 0) {
      points.push({
        day: day + 1,
        susceptible: nextSusceptible,
        exposed: nextExposed,
        infectious: nextInfectious,
        recovered: nextRecovered,
        deaths: nextDeaths,
      });
      break;
    }

    susceptible = nextSusceptible;
    exposed = nextExposed;
    infectious = nextInfectious;
    recovered = nextRecovered;
    deaths = nextDeaths;
    day += 1;
  }

  return points;
}

export function calculateFactorMultiplier(network: NetworkData | null, dataFactors: DataFactor[]): number {
  const activeFactors = dataFactors.filter((factor) => factor.enabled);
  if (!network || activeFactors.length === 0) {
    return 1;
  }

  const profiles = network.nodes
    .map((node) => node.profile)
    .filter((profile): profile is NonNullable<NetworkData['nodes'][number]['profile']> => Boolean(profile));

  if (profiles.length === 0) {
    // Als er geen profielen beschikbaar zijn, gebruiken we generieke gemiddelden
    // zodat de factorinstellingen toch direct effect hebben op de simulatie.
  }

  const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));
  const normalize = (value: number, min: number, max: number) => (min === max ? 0 : clamp((value - min) / (max - min), 0, 1));
  const average = (values: number[]) => (values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length);
  const mapFactor = (normalized: number, minFactor: number, maxFactor: number) => minFactor + normalized * (maxFactor - minFactor);

  const hasProfiles = profiles.length > 0;
  const averagePopulation = hasProfiles ? average(profiles.map((profile) => profile.bevolkingsomvang)) : 6000;
  const averageHouseholdSize = hasProfiles ? average(profiles.map((profile) => profile.huishoudgrootte)) : 2.5;
  const averageNonWestern = hasProfiles ? average(profiles.map((profile) => profile.aandeelNietWesterseAchtergrond)) : 20;
  const averageApartmentShare = hasProfiles ? average(profiles.map((profile) => (profile.woningtype === 'appartement' ? 1 : 0))) : 0.5;
  const averageOccupancy = hasProfiles ? average(profiles.map((profile) => profile.bezettingsgraadWoning)) : 1.7;
  const averageIncome = hasProfiles ? average(profiles.map((profile) => profile.gemiddeldBestedbaarInkomen)) : 35000;
  const averageUrbanity = hasProfiles ? average(profiles.map((profile) => profile.stedelijkheidsgraad)) : 60;
  const averageLowEducation = hasProfiles ? average(profiles.map((profile) => profile.opleidingsniveau.laag)) : 0.3;
  const averageChildShare = hasProfiles ? average(profiles.map((profile) => (profile.leeftijd <= 14 ? 1 : 0))) : 0.18;
  const averageSeniorShare = hasProfiles ? average(profiles.map((profile) => (profile.leeftijd >= 65 ? 1 : 0))) : 0.18;

  const factorEffects = activeFactors.map((factor) => {
    const mapRange = (normalized: number) => mapFactor(normalized, factor.minFactor, factor.maxFactor);

    if (factor.label.includes('Bevolkingsomvang')) {
      return mapRange(normalize(averagePopulation, 1000, 12000));
    }
    if (factor.label.includes('Leeftijd')) {
      const seniorRisk = mapFactor(normalize(averageSeniorShare * 100, 5, 30), 1, 1.5);
      const childRisk = mapFactor(normalize(averageChildShare * 100, 5, 30), 1, 1.2);
      const ageRisk = clamp(1 + (seniorRisk - 1) + (childRisk - 1), 0.5, 1.5);
      return mapRange(normalize(ageRisk, 0.5, 1.5));
    }
    if (factor.label.includes('Huishoudgrootte')) {
      return mapRange(normalize(averageHouseholdSize, 1.2, 3.1));
    }
    if (factor.label.includes('aandeel niet-westerse')) {
      return mapRange(normalize(averageNonWestern, 5, 40));
    }
    if (factor.label.includes('Woningtype')) {
      return mapRange(averageApartmentShare);
    }
    if (factor.label.includes('Bezettingsgraad')) {
      return mapRange(normalize(averageOccupancy, 1.1, 2.4));
    }
    if (factor.label.includes('Inkomen')) {
      return mapRange(1 - normalize(averageIncome, 22000, 72000));
    }
    if (factor.label.includes('Stedelijkheidsgraad')) {
      return mapRange(normalize(averageUrbanity, 20, 100));
    }
    if (factor.label.includes('Opleidingsniveau')) {
      return mapRange(normalize(averageLowEducation, 0.18, 0.42));
    }
    return 1;
  });

  const multiplier = factorEffects.reduce((acc, effect) => acc * effect, 1);
  return clamp(multiplier, 0.6, 1.5);
}
