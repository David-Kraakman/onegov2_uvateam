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

- `src/main.tsx`: alle React-schermen, navigatie, configuratievelden en de `Run Sim` knop.
- `src/styles.css`: globale styling, liquid-glass effect, scrollbar, buttons en input-styling.
- `src/data/utrechtData.ts`: plek om Utrecht-data, CBS-tabellen, buurten, RWZI-data of netwerkmetadata in te plakken.
- `index.html`: Google Font import en root-element.
- `tailwind.config.ts`: Tailwind-configuratie, inclusief Inter als standaard sans-serif font.

## Run Sim aanpassen

De configuratiepagina staat in `src/main.tsx` in de component:

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

Het uploadveld voor het netwerk staat ook in `SimulationConfiguration`. Het accepteert JSON en CSV:

```tsx
accept=".json,.csv,application/json,text/csv"
```

Momenteel wordt alleen de bestandsnaam opgeslagen. Als je de inhoud wilt gebruiken, moet je in de `onChange` handler het bestand uitlezen met `file.text()` en daarna JSON of CSV parsen.

