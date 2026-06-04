# Sick Sim

Sick Sim is een React + TypeScript + Tailwind dashboard voor het configureren en starten van een epidemiologische simulatie voor Utrecht.

## Starten

Installeer dependencies:

```bash
npm install
```

Start de dev-server:

```bash
npm run dev
```

Maak een productiebuild:

```bash
npm run build
```

## Belangrijke bestanden

- `src/main.tsx`: startpunt van React; rendert alleen de app.
- `src/App.tsx`: hoofdscherm, actieve pagina en navigatie tussen pagina's.
- `src/pages/SimulationConfiguration.tsx`: configuratieformulier en de `Run Sim` knop.
- `src/pages/SimulationRun.tsx`: scherm dat je ziet na `Run Sim`.
- `src/pages/NetworkGeneration.tsx`: netwerkvisualisatie en netwerkstatistieken.
- `src/pages/PipelineOverview.tsx`: pipeline-uitleg.
- `src/components/BackgroundVideo.tsx`: achtergrondvideo en pauzeren op het eindframe.
- `src/components/Navbar.tsx`: bovenste navigatiebalk.
- `src/components/FormControls.tsx`: gedeelde formuliervelden, titel en sliders.
- `src/components/DataFactorRow.tsx`: losse rij voor een aan/uit datafactor.
- `src/components/NetworkCanvas.tsx`: mock-netwerkcanvas.
- `src/components/SeirChart.tsx`: mock-SEIR grafiek.
- `src/constants/appConstants.ts`: URLs, navigatiepagina's en datafactor-labels.
- `src/utils/generateNetwork.ts`: functie om een synthetisch Utrecht-netwerk te genereren.
- `src/styles.css`: globale styling, liquid-glass effect, scrollbar, buttons en input-styling.
- `src/data/utrechtData.ts`: plek om Utrecht-data, CBS-tabellen, buurten, RWZI-data of netwerkmetadata in te plakken.
- `index.html`: Google Font import en root-element.
- `tailwind.config.ts`: Tailwind-configuratie, inclusief Inter als standaard sans-serif font.

## Run Sim aanpassen

De configuratiepagina staat in `src/pages/SimulationConfiguration.tsx` in de component:

```tsx
function SimulationConfiguration({ onRun }: { onRun: () => void }) {
```

De knop zelf staat onderaan die component:

```tsx
<button className="control-button" onClick={onRun}>
  <Play size={16} /> Run Sim
</button>
```

Op dit moment wisselt `onRun` alleen naar het simulatiescherm. Dat gebeurt in de hoofdcomponent:

```tsx
// src/App.tsx
{activePage === 'Simulatie' && <SimulationConfiguration onRun={() => goToPage('Simulatie run')} />}
```

Als je echte simulatiecode wilt starten, kun je daar een functie tussen zetten, bijvoorbeeld:

```tsx
const runSimulation = () => {
  // Lees configuratie uit state
  // Parse netwerkbestand
  // Bereken SEIR-stappen
  goToPage('Simulatie run');
};
```

Daarna geef je die functie door:

```tsx
<SimulationConfiguration onRun={runSimulation} />
```

## Netwerkbestand

Het uploadveld voor het netwerk staat in `src/pages/SimulationConfiguration.tsx`. Het accepteert JSON en CSV:

```tsx
accept=".json,.csv,application/json,text/csv"
```

Na upload wordt het bestand geparsed in `src/utils/networkParser.ts`. De netwerkdata wordt opgeslagen in `src/App.tsx` en daarna doorgegeven aan:

- `src/pages/NetworkGeneration.tsx`: toont echte knopen, verbindingen en statistieken.
- `src/pages/SimulationRun.tsx`: berekent een eenvoudige SEIR-curve op basis van het netwerk en de ingestelde parameters.

JSON kan bijvoorbeeld zo:

```json
{
  "nodes": [
    { "id": "A", "label": "Buurt A" },
    { "id": "B", "label": "Buurt B" }
  ],
  "edges": [
    { "source": "A", "target": "B", "weight": 1 }
  ]
}
```

CSV kan bijvoorbeeld zo:

```csv
source,target,weight
A,B,1
B,C,0.7
```

De parser herkent ook kolommen zoals `from,to`.
