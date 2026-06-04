import { GitBranch } from 'lucide-react';
import { repoUrl } from '../constants/appConstants';
import { utrechtData } from '../data/utrechtData';

export function PipelineOverview() {
  const cards = [
    ['CBS-extractie', 'CBS-tabellen zoals 86165NED, 82275NED en 70262NED worden per Utrechtse buurtcode opgeschoond en gestandaardiseerd.'],
    ['Synthetische populatie', 'Huishoudens, leeftijden, woningtype en stedelijkheid vormen agenten met lokale contactkansen.'],
    ['RWZI-koppeling', 'Afvalwaterzuivering, stroomgebieden en aansluitingen verbinden ruimtelijke observaties aan transmissieclusters.'],
  ];

  return (
    <div className="mx-auto flex w-full max-w-6xl items-center py-8">
      <div className="liquid-glass w-full rounded-2xl p-8 md:p-10">
        <div className="relative z-10 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-gray-300">Systeemarchitectuur</p>
            <h1 className="mb-5 text-4xl font-normal tracking-tight md:text-5xl">Pipeline overzicht</h1>
            <p className="max-w-2xl text-base leading-7 text-gray-300">
              Sick Sim zet ruwe Utrechtse CBS-, RWZI- en landgebruiksdata om naar een synthetische populatie, genereert contactnetwerken en draait daarna een configureerbare SEIR-simulatie.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-gray-300">
              Huidige datalocatie: <span className="text-white">{utrechtData.location}</span>. De app verwacht straks wijk-, buurt- en factorwaarden vanuit het databestand in <span className="text-white">src/data/utrechtData.ts</span>.
            </p>
            <a href={repoUrl} target="_blank" rel="noreferrer" className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2 text-sm font-medium text-black transition hover:bg-gray-100">
              <GitBranch size={16} /> Open GitHub-project
            </a>
          </div>
          <div className="grid gap-4">
            {cards.map(([title, text], index) => (
              <article className="fade-card rounded-lg border border-white/15 bg-black/35 p-5" style={{ animationDelay: `${index * 90}ms` }} key={title}>
                <h2 className="mb-2 text-lg font-medium">{title}</h2>
                <p className="text-sm leading-6 text-gray-300">{text}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
