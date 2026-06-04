import React from 'react';
import ReactDOM from 'react-dom/client';
import { Activity, BarChart3, Code2, Database, Download, FileUp, GitBranch, Map, Pause, Play, RotateCcw } from 'lucide-react';
import { utrechtData } from './data/utrechtData';
import './styles.css';

const videoUrl = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260403_050628_c4e32401-fab4-4a27-b7a8-6e9291cd5959.mp4';
const repoUrl = 'https://github.com/';

type Page = 'Pipeline overzicht' | 'Netwerk genereren' | 'Simulatie' | 'Simulatie run';

const navigationPages: Page[] = ['Pipeline overzicht', 'Netwerk genereren', 'Simulatie'];

const factorLabels = [
  'Buurtcode / wijkcode (BU/WK) [Ruimtelijk / Sociaal]',
  'Bevolkingsomvang per buurt [Demografie / Epidemiologie] (86165NED)',
  'Leeftijdsverdeling (0-14 / 15-24 / 25-44 / 45-64 / 65+) [Demografie / Epidemiologie] (86165NED)',
  'Huishoudgrootte en -samenstelling [Demografie / Epidemiologie] (86165NED)',
  'Aandeel niet-westerse achtergrond [Demografie / Sociaal] (86165NED)',
  'Woningtype (appartement / rijtjeshuis / vrijstaand) [Wonen / Epidemiologie] (86165NED)',
  'Bezettingsgraad woning (personen per woning) [Wonen / Epidemiologie] (86165NED)',
  'Gemiddeld besteedbaar inkomen per huishouden [Sociaal-economisch / Sociaal] (86165NED)',
  'Stedelijkheidsgraad / urban-rural classificatie [Ruimtelijk / Epidemiologie] (86165NED)',
  'Opleidingsniveau (laag / midden / hoog, % bevolking 25+) [Sociaal-economisch / Sociaal] (82275NED)',
  'RWZI-ID, naam, locatie, capaciteit [Ruimtelijk / Metadata] (RWZI-register)',
  'Catchment-oppervlak en aansluitingen [Ruimtelijk / Metadata] (RWZI-stroomgebiedskaart)',
  'Landgebruik: aandeel woongebied (% oppervlak) [Landgebruik / Metadata] (70262NED)',
  'Landgebruik: aandeel industrie / bedrijventerrein (%) [Landgebruik / Metadata] (70262NED)',
  'Landgebruik: aandeel agrarisch (%) [Landgebruik / Metadata] (70262NED)',
  'Nabijheid (lucht)haven (km tot dichtstbijzijnde) [Ruimtelijk / Metadata] (85870NED)',
];

type DataFactor = {
  label: string;
  enabled: boolean;
  weight: number;
};

function App() {
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
      <PingPongVideo />
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

function PingPongVideo() {
  const videoRef = React.useRef<HTMLVideoElement | null>(null);

  React.useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;

    let frame = 0;
    const edgeBuffer = 0.18;

    const tick = () => {
      const duration = video.duration;

      if (Number.isFinite(duration) && duration > 0) {
        if (video.currentTime >= duration - edgeBuffer) {
          video.currentTime = duration - edgeBuffer;
          video.pause();
          return;
        }
      }

      frame = window.requestAnimationFrame(tick);
    };

    void video.play();
    frame = window.requestAnimationFrame(tick);

    return () => window.cancelAnimationFrame(frame);
  }, []);

  return <video ref={videoRef} className="absolute inset-0 h-full w-full object-cover" src={videoUrl} autoPlay muted playsInline />;
}

function Navbar({ activePage, onPageChange }: { activePage: Page; onPageChange: (page: Page) => void }) {
  return (
    <nav className="liquid-glass shrink-0 rounded-xl px-6 py-3">
      <div className="relative z-10 flex items-center justify-between gap-6">
        <button className="text-2xl font-semibold tracking-tight" onClick={() => onPageChange('Simulatie')}>Sick Sim</button>
        <div className="hidden items-center gap-8 md:flex">
          {navigationPages.map((page) => (
            <button key={page} onClick={() => onPageChange(page)} className={`border-b py-1 text-sm transition hover:text-gray-300 ${activePage === page || (page === 'Simulatie' && activePage === 'Simulatie run') ? 'border-white text-white' : 'border-transparent text-white/70'}`}>
              {page}
            </button>
          ))}
        </div>
        <a href={repoUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2 text-sm font-medium text-black transition hover:bg-gray-100">
          <Code2 size={16} /> GitHub-code
        </a>
      </div>
    </nav>
  );
}

function PipelineOverview() {
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

function NetworkGeneration() {
  return (
    <div className="mx-auto grid w-full max-w-6xl items-center gap-6 py-8 lg:grid-cols-[1fr_320px]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10 h-full">
          <h1 className="mb-4 text-3xl font-normal tracking-tight">Netwerk genereren</h1>
          <NetworkCanvas />
        </div>
      </div>
      <aside className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h2 className="mb-5 flex items-center gap-2 text-lg font-medium"><BarChart3 size={18} /> Netwerkstatistieken</h2>
          {[
            ['Knopen', '1.248'],
            ['Verbindingen', '7.931'],
            ['Gemiddelde graad', '12,7'],
            ['Clustering', '0,42'],
            ['Huishoudcontacten', '38%'],
          ].map(([label, value]) => (
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3 text-sm" key={label}>
              <span className="text-gray-300">{label}</span>
              <span className="font-medium">{value}</span>
            </div>
          ))}
          <button className="liquid-glass mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-medium transition hover:text-gray-300">
            <Download size={16} /> Download netwerk (JSON/CSV)
          </button>
        </div>
      </aside>
    </div>
  );
}

function NetworkCanvas() {
  const nodes = Array.from({ length: 22 }, (_, i) => {
    const angle = (i / 22) * Math.PI * 2;
    const radius = i % 3 === 0 ? 185 : 120 + (i % 5) * 12;
    return { x: 300 + Math.cos(angle) * radius, y: 240 + Math.sin(angle) * radius };
  });

  return (
    <svg viewBox="0 0 600 480" className="h-[480px] w-full rounded-lg border border-white/10 bg-black/30">
      {nodes.map((node, i) => nodes.slice(i + 1, i + 4).map((target, j) => (
        <line key={`${i}-${j}`} x1={node.x} y1={node.y} x2={target.x} y2={target.y} stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
      )))}
      {nodes.map((node, i) => (
        <circle key={i} cx={node.x} cy={node.y} r={i % 4 === 0 ? 8 : 5} fill="white" opacity={i % 4 === 0 ? 0.95 : 0.65} />
      ))}
    </svg>
  );
}

function SimulationConfiguration({ onRun }: { onRun: () => void }) {
  const [immune, setImmune] = React.useState(true);
  const [networkFileName, setNetworkFileName] = React.useState('');
  const [dataFactors, setDataFactors] = React.useState<DataFactor[]>(
    factorLabels.map((label, index) => ({ label, enabled: index < 10, weight: index % 4 === 0 ? 1.4 : 1 })),
  );

  const updateFactor = (index: number, patch: Partial<DataFactor>) => {
    setDataFactors((current) => current.map((factor, factorIndex) => factorIndex === index ? { ...factor, ...patch } : factor));
  };

  return (
    <div className="flex min-h-0 w-full items-center justify-center py-8">
      <div className="flex max-h-full w-full max-w-4xl flex-col text-center">
        <AnimatedTitle text="Sick Sim" />
        <div className="liquid-glass min-h-0 w-full rounded-2xl border border-white/20 p-6 text-left md:p-8">
          <div className="custom-scrollbar relative z-10 max-h-[60vh] overflow-y-auto pr-2">
            <SectionTitle icon={<Activity size={18} />} title="Epidemiologische variabelen" />
            <div className="grid gap-5 md:grid-cols-2">
              <Field label="Netwerk" hint="Voeg hier een netwerkbestand toe in JSON- of CSV-formaat.">
                <label className="flex min-h-[48px] cursor-pointer items-center justify-between gap-3 rounded-lg border border-white/15 bg-black/40 px-3 py-2 transition hover:border-white/30 hover:bg-black/55">
                  <span className="min-w-0 truncate text-sm text-gray-300">
                    {networkFileName || 'Nog geen netwerkbestand geselecteerd'}
                  </span>
                  <span className="inline-flex shrink-0 items-center gap-2 rounded-md bg-white px-3 py-2 text-xs font-medium text-black">
                    <FileUp size={15} /> Upload
                  </span>
                  <input
                    className="sr-only"
                    type="file"
                    accept=".json,.csv,application/json,text/csv"
                    onChange={(event) => setNetworkFileName(event.target.files?.[0]?.name ?? '')}
                  />
                </label>
              </Field>
              <Range label="Basis transmissie per contact (beta)" hint="Kans dat iemand besmet raakt bij 1 contact" min={0} max={1} step={0.01} initialValue={0.28} decimals={2} />
              <Field label="Incubatietijd" hint="Tijd voordat iemand besmettelijk wordt in dagen"><input type="number" defaultValue={3} /></Field>
              <Field label="Besmettelijke periode" hint="Hoe lang iemand anderen kan besmetten in dagen"><input type="number" defaultValue={6} /></Field>
              <Range label="Asymptomatisch percentage" hint="Deel dat ziek is maar niet merkbaar" min={0} max={100} step={1} initialValue={32} suffix="%" />
              <Field label="Ziekte-ernst" hint="Beinvloedt gedrag: mate waarin mensen thuisblijven"><select><option>Matig</option><option>Laag</option><option>Hoog</option></select></Field>
              <Range label="Herstelkans per dag" min={0} max={1} step={0.01} initialValue={0.18} decimals={2} />
              <div className="rounded-lg border border-white/10 bg-black/25 p-4">
                <label className="mb-3 flex items-center justify-between text-sm font-medium">
                  Immuniteit na infectie
                  <span className="flex items-center gap-2 text-xs text-gray-300">
                    {immune ? 'Ja' : 'Nee'}
                    <input className="h-5 w-5 accent-white" type="checkbox" checked={immune} onChange={(event) => setImmune(event.target.checked)} />
                  </span>
                </label>
                {immune && <input type="number" defaultValue={120} aria-label="Duur immuniteit in dagen" />}
              </div>
            </div>

            <SectionTitle icon={<Database size={18} />} title="Datafactoren" />
            <div className="grid gap-3">
              {dataFactors.map((factor, index) => (
                <DataFactorRow
                  factor={factor}
                  index={index}
                  key={factor.label}
                  onEnabledChange={(enabled) => updateFactor(index, { enabled })}
                  onWeightChange={(weight) => updateFactor(index, { weight })}
                />
              ))}
            </div>

            <div className="sticky bottom-0 mt-6 flex justify-end bg-black/70 py-4 backdrop-blur">
              <button className="control-button" onClick={onRun}><Play size={16} /> Run Sim</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DataFactorRow({ factor, onEnabledChange, onWeightChange }: { factor: DataFactor; index: number; onEnabledChange: (enabled: boolean) => void; onWeightChange: (weight: number) => void }) {
  return (
    <div className={`grid gap-3 rounded-lg border p-4 transition md:grid-cols-[1fr_86px_220px] ${factor.enabled ? 'border-white/10 bg-black/25 text-white' : 'border-white/5 bg-neutral-900/70 text-gray-500'}`}>
      <span className="text-sm">{factor.label}</span>
      <label className="flex items-center gap-2 text-xs">
        <input type="checkbox" className="h-4 w-4 accent-white" checked={factor.enabled} onChange={(event) => onEnabledChange(event.target.checked)} />
        {factor.enabled ? 'Aan' : 'Uit'}
      </label>
      <label className="grid gap-1 text-xs">
        <span className="flex justify-between">
          <span>Gewicht</span>
          <span>{factor.weight.toFixed(1)}x</span>
        </span>
        <input disabled={!factor.enabled} type="range" min="0" max="2" step="0.1" value={factor.weight} onChange={(event) => onWeightChange(Number(event.target.value))} aria-label={`${factor.label} gewichtsfactor`} />
      </label>
    </div>
  );
}

function AnimatedTitle({ text }: { text: string }) {
  return (
    <h1 className="mb-6 shrink-0 text-4xl font-normal tracking-tight md:text-5xl lg:text-6xl" style={{ letterSpacing: '-0.04em' }}>
      {text.split('').map((char, index) => (
        <span className="inline-block animate-letter" style={{ animationDelay: `${index * 45}ms` }} key={`${char}-${index}`}>{char === ' ' ? '\u00a0' : char}</span>
      ))}
    </h1>
  );
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return <h2 className="mb-4 mt-8 flex items-center gap-2 text-xl font-medium first:mt-0">{icon}{title}</h2>;
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block rounded-lg border border-white/10 bg-black/25 p-4">
      <span className="mb-2 block text-sm font-medium">{label}</span>
      {children}
      {hint && <span className="mt-2 block text-xs leading-5 text-gray-300">{hint}</span>}
    </label>
  );
}

function Range({ label, hint, min, max, step, initialValue, suffix = '', decimals }: { label: string; hint?: string; min: number; max: number; step: number; initialValue: number; suffix?: string; decimals?: number }) {
  const [value, setValue] = React.useState(initialValue);
  const displayValue = decimals === undefined ? String(value) : value.toFixed(decimals);

  return (
    <Field label={label} hint={hint}>
      <div className="grid gap-2">
        <div className="flex justify-between text-xs text-gray-300">
          <span>{min}{suffix}</span>
          <span className="rounded bg-white px-2 py-1 font-medium text-black">{displayValue}{suffix}</span>
          <span>{max}{suffix}</span>
        </div>
        <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => setValue(Number(event.target.value))} />
      </div>
    </Field>
  );
}

function SimulationRun() {
  return (
    <div className="mx-auto grid w-full max-w-6xl items-center gap-6 py-8 lg:grid-cols-[1fr_0.9fr]">
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h1 className="mb-5 flex items-center gap-2 text-3xl font-normal tracking-tight"><Activity size={24} /> Simulatie</h1>
          <SeirChart />
          <div className="mt-5 flex gap-3">
            <button className="control-button"><Play size={16} /> Start</button>
            <button className="control-button"><Pause size={16} /> Pauze</button>
            <button className="control-button"><RotateCcw size={16} /> Reset</button>
          </div>
        </div>
      </div>
      <div className="liquid-glass rounded-2xl p-6">
        <div className="relative z-10">
          <h2 className="mb-5 flex items-center gap-2 text-xl font-medium"><Map size={20} /> Transmissieverdeling in Utrecht</h2>
          <div className="relative h-[420px] overflow-hidden rounded-lg border border-white/10 bg-black/35">
            {Array.from({ length: 26 }, (_, i) => (
              <span key={i} className="absolute rounded-full bg-white" style={{ left: `${8 + (i * 31) % 84}%`, top: `${12 + (i * 47) % 74}%`, width: `${10 + (i % 5) * 8}px`, height: `${10 + (i % 5) * 8}px`, opacity: 0.18 + (i % 6) * 0.09 }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SeirChart() {
  const paths = [
    'M20 250 C90 230, 120 170, 180 145 S290 100, 380 115 S480 170, 560 160',
    'M20 280 C100 275, 135 220, 210 200 S320 140, 410 175 S500 245, 560 235',
    'M20 310 C90 308, 170 285, 240 240 S350 210, 430 250 S510 300, 560 292',
    'M20 330 C130 330, 200 325, 300 290 S450 250, 560 205',
  ];
  const labels = ['Vatbaar', 'Besmet', 'Infectieus', 'Hersteld'];

  return (
    <svg viewBox="0 0 580 360" className="h-[360px] w-full rounded-lg border border-white/10 bg-black/35">
      {[80, 150, 220, 290].map((y) => <line key={y} x1="20" x2="560" y1={y} y2={y} stroke="rgba(255,255,255,0.1)" />)}
      {paths.map((path, index) => <path key={path} d={path} fill="none" stroke="white" strokeWidth={index === 0 ? 3 : 2} opacity={1 - index * 0.18} />)}
      {labels.map((label, index) => <text key={label} x={28 + index * 126} y="335" fill="rgba(255,255,255,0.72)" fontSize="13">{label}</text>)}
    </svg>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
