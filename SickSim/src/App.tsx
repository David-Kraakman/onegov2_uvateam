import React from 'react';
import { BackgroundVideo } from './components/BackgroundVideo';
import { Navbar } from './components/Navbar';
import { NetworkGeneration } from './pages/NetworkGeneration';
import { PipelineOverview } from './pages/PipelineOverview';
import { SimulationConfiguration } from './pages/SimulationConfiguration';
import { SimulationRun } from './pages/SimulationRun';
import type { Page } from './types';

export function App() {
  const [activePage, setActivePage] = React.useState<Page>('Simulatie');
  const [loaded, setLoaded] = React.useState(false);

  React.useEffect(() => {
    const timer = window.setTimeout(() => setLoaded(true), 120);
    return () => window.clearTimeout(timer);
  }, [activePage]);

  const goToPage = (page: Page) => {
    setLoaded(false);
    setActivePage(page);
  };

  return (
    <main className="relative h-screen overflow-hidden bg-black text-white">
      <BackgroundVideo />
      <div className="relative z-10 flex h-screen min-h-0 flex-col px-6 pt-6 md:px-12 lg:px-16">
        <Navbar activePage={activePage} onPageChange={goToPage} />
        <section className={`flex min-h-0 flex-1 transition-all duration-500 ${loaded ? 'translate-y-0 opacity-100' : 'translate-y-3 opacity-0'}`}>
          {activePage === 'Pipeline overzicht' && <PipelineOverview />}
          {activePage === 'Netwerk genereren' && <NetworkGeneration />}
          {activePage === 'Simulatie' && <SimulationConfiguration onRun={() => goToPage('Simulatie run')} />}
          {activePage === 'Simulatie run' && <SimulationRun />}
        </section>
      </div>
    </main>
  );
}
