import React from 'react';
import { Activity, Database, FileUp, Play } from 'lucide-react';
import { AnimatedTitle, Field, Range, SectionTitle } from '../components/FormControls';
import { DataFactorRow } from '../components/DataFactorRow';
import { factorLabels } from '../constants/appConstants';
import type { DataFactor, NetworkData, SimulationConfig } from '../types';
import { parseNetworkFile } from '../utils/networkParser';

type SimulationConfigurationProps = {
  config: SimulationConfig;
  network: NetworkData | null;
  dataFactors: DataFactor[];
  onConfigChange: (config: SimulationConfig) => void;
  onDataFactorsChange: (dataFactors: DataFactor[]) => void;
  onNetworkLoaded: (network: NetworkData) => void;
  onRun: () => void;
};

export function SimulationConfiguration({ config, network, dataFactors, onConfigChange, onDataFactorsChange, onNetworkLoaded, onRun }: SimulationConfigurationProps) {
  const [networkStatus, setNetworkStatus] = React.useState('');

  const updateConfig = (patch: Partial<SimulationConfig>) => {
    onConfigChange({ ...config, ...patch });
  };

  const handleNetworkUpload = async (file: File | undefined) => {
    if (!file) return;

    setNetworkStatus('Netwerk wordt ingelezen...');
    try {
      const parsedNetwork = await parseNetworkFile(file);
      onNetworkLoaded(parsedNetwork);
      setNetworkStatus(`${parsedNetwork.fileName} geladen: ${parsedNetwork.nodes.length} knopen, ${parsedNetwork.edges.length} verbindingen`);
    } catch (error) {
      setNetworkStatus(error instanceof Error ? error.message : 'Netwerkbestand kon niet worden gelezen.');
    }
  };

  const updateFactor = (index: number, patch: Partial<DataFactor>) => {
    onDataFactorsChange(dataFactors.map((factor, factorIndex) => {
      if (factorIndex !== index) {
        return factor;
      }

      const updatedFactor = { ...factor, ...patch };
      const minFactor = Math.max(0, Math.min(updatedFactor.minFactor, updatedFactor.maxFactor));
      const maxFactor = Math.max(minFactor, updatedFactor.maxFactor);

      return { ...updatedFactor, minFactor, maxFactor };
    }));
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
                    {network?.fileName || 'Nog geen netwerkbestand geselecteerd'}
                  </span>
                  <span className="inline-flex shrink-0 items-center gap-2 rounded-md bg-white px-3 py-2 text-xs font-medium text-black">
                    <FileUp size={15} /> Upload
                  </span>
                  <input
                    className="sr-only"
                    type="file"
                    accept=".json,.csv,application/json,text/csv"
                    onChange={(event) => void handleNetworkUpload(event.target.files?.[0])}
                  />
                </label>
                {networkStatus && <span className="mt-2 block text-xs text-gray-300">{networkStatus}</span>}
              </Field>
              <Range
                label="Basis transmissie per contact (beta)"
                hint="Kans dat iemand besmet raakt bij 1 contact, in procenten"
                min={0}
                max={100}
                step={1}
                initialValue={config.beta}
                suffix="%"
                onValueChange={(beta) => updateConfig({ beta })}
              />
              <Field label="Incubatietijd" hint="Tijd voordat iemand besmettelijk wordt in dagen"><input type="number" value={config.incubationDays} onChange={(event) => updateConfig({ incubationDays: Number(event.target.value) })} /></Field>
              <Field label="Besmettelijke periode" hint="Gemiddeld aantal dagen dat iemand anderen kan besmetten"><input type="number" value={config.infectiousDays} onChange={(event) => updateConfig({ infectiousDays: Number(event.target.value) })} /></Field>
              <Range
                label="Asymptomatisch percentage"
                hint="Deel dat ziek is maar niet merkbaar; verhoogt verborgen verspreiding"
                min={0}
                max={100}
                step={1}
                initialValue={config.asymptomaticPercentage}
                suffix="%"
                onValueChange={(asymptomaticPercentage) => updateConfig({ asymptomaticPercentage })}
              />
              <Range
                label="Herstelkans per dag"
                hint="Dagelijkse kans op herstel; wordt gecombineerd met de infectieuze duur"
                min={0}
                max={100}
                step={1}
                initialValue={config.recoveryChance}
                suffix="%"
                onValueChange={(recoveryChance) => updateConfig({ recoveryChance })}
              />
              <Range
                label="Letaliteit"
                hint="Kans dat een infectie fataal wordt"
                min={0}
                max={100}
                step={1}
                initialValue={config.lethalityChance}
                suffix="%"
                onValueChange={(lethalityChance) => updateConfig({ lethalityChance })}
              />
              <Range
                label="Immuniteit kans na infectie"
                hint="Kans dat iemand immuun blijft na herstel"
                min={0}
                max={100}
                step={1}
                initialValue={config.immunityChance}
                suffix="%"
                onValueChange={(immunityChance) => updateConfig({ immunityChance })}
              />
            </div>

            <SectionTitle icon={<Database size={18} />} title="Datafactoren" />
            <p className="mb-3 text-sm text-gray-300">
              De minimale factor bepaalt de ondergrens van het transmissie-effect, de maximale factor bepaalt de bovengrens. Verander beide om de range van elk datafactor-effect in te stellen.
            </p>
            <div className="grid gap-3">
              {dataFactors.map((factor, index) => (
                <DataFactorRow
                  factor={factor}
                  key={factor.label}
                  onEnabledChange={(enabled) => updateFactor(index, { enabled })}
                  onMinFactorChange={(minFactor) => updateFactor(index, { minFactor })}
                  onMaxFactorChange={(maxFactor) => updateFactor(index, { maxFactor })}
                />
              ))}
            </div>

            <div className="sticky bottom-0 mt-6 flex justify-end py-4">
  <button className="control-button" onClick={onRun}>
    <Play size={16} /> Start Sim
  </button>
</div>
          </div>
        </div>
      </div>
    </div>
  );
}
