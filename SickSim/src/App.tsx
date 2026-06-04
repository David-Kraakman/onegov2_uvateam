import React from 'react';
import { BackgroundVideo } from './components/BackgroundVideo';
import { Navbar } from './components/Navbar';
import { NetworkGeneration } from './pages/NetworkGeneration';
import { PipelineOverview } from './pages/PipelineOverview';
import { SimulationConfiguration } from './pages/SimulationConfiguration';
import { SimulationRun } from './pages/SimulationRun';
import { factorLabels } from './constants/appConstants';
import type { DataFactor, NetworkData, Page, SimulationConfig } from './types';

export function App() {
  const [activePage, setActivePage] = React.useState<Page>('Simulatie');
  const [loaded, setLoaded] = React.useState(false);
  const [network, setNetwork] = React.useState<NetworkData | null>(null);
  const [simulationConfig, setSimulationConfig] = React.useState<SimulationConfig>({
    beta: 28,
    incubationDays: 3,
    infectiousDays: 6,
    recoveryChance: 18,
    asymptomaticPercentage: 32,
    immunityChance: 100,
    lethalityChance: 0,
  });
  const [dataFactors, setDataFactors] = React.useState<DataFactor[]>(
    factorLabels.map((label, index) => ({
      label,
      enabled: index < 10,
      minFactor: 0.8,
      maxFactor: 1.5,
    })),
  );

  React.useEffect(() => {
    const timer = window.setTimeout(() => setLoaded(true), 120);
    return () => window.clearTimeout(timer);
  }, [activePage]);

  const [lastSimulationPage, setLastSimulationPage] = React.useState<Page>('Simulatie');

  const goToPage = (page: Page, forceSimulationConfig = false) => {
    if (page === activePage || (page === 'Simulatie' && activePage === 'Simulatie run' && !forceSimulationConfig)) {
      return;
    }

    const nextPage = page === 'Simulatie' && lastSimulationPage === 'Simulatie run' && !forceSimulationConfig
      ? 'Simulatie run'
      : page;

    setLoaded(false);
    setActivePage(nextPage);
  };

  return (
    <main className="relative h-screen overflow-hidden bg-black text-white">
      <BackgroundVideo />
      <div className="relative z-10 flex h-screen min-h-0 flex-col px-6 pt-6 md:px-12 lg:px-16">
        <Navbar activePage={activePage} onPageChange={goToPage} />
        <section className={`flex min-h-0 flex-1 transition-all duration-500 ${loaded ? 'translate-y-0 opacity-100' : 'translate-y-3 opacity-0'}`}>
          {activePage === 'Pipeline overzicht' && <PipelineOverview />}
          {activePage === 'Netwerk genereren' && <NetworkGeneration network={network} onNetworkGenerated={setNetwork} />}
          {activePage === 'Simulatie' && (
            <SimulationConfiguration
              config={simulationConfig}
              network={network}
              dataFactors={dataFactors}
              onConfigChange={setSimulationConfig}
              onDataFactorsChange={setDataFactors}
              onNetworkLoaded={setNetwork}
              onRun={() => {
                setLastSimulationPage('Simulatie run');
                goToPage('Simulatie run');
              }}
            />
          )}
          {activePage === 'Simulatie run' && (
            <SimulationRun
              config={simulationConfig}
              dataFactors={dataFactors}
              network={network}
              onBack={() => {
                setLastSimulationPage('Simulatie');
                goToPage('Simulatie', true);
              }}
            />
          )}
        </section>
      </div>
    </main>
  );
}
