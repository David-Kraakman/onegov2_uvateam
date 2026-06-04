import type { DataFactor } from '../types';

type DataFactorRowProps = {
  factor: DataFactor;
  onEnabledChange: (enabled: boolean) => void;
  onMinFactorChange: (minFactor: number) => void;
  onMaxFactorChange: (maxFactor: number) => void;
};

function getFactorDescription(label: string) {
  if (label.includes('Buurtcode / wijkcode')) {
    return 'De minimale factor bepaalt de laagste transmissie-impact; de maximale factor bepaalt de hoogste transmissie-impact voor ruimtelijke spreiding.';
  }
  if (label.includes('Bevolkingsomvang')) {
    return 'De minimale factor bepaalt de ondergrens van het effect van bevolkingsomvang; de maximale factor bepaalt de bovengrens.';
  }
  if (label.includes('Leeftijdsverdeling')) {
    return 'Leeftijdsverdeling kan de transmissie richting ouderen verhogen. Min factor bepaalt de ondergrens; max factor bepaalt de bovengrens. Kinderen krijgen geen lager risico omdat zij juist kwetsbaar zijn.';
  }
  if (label.includes('Huishoudgrootte')) {
    return 'Huishoudgrootte kan het infectierisico vergroten. Min factor geeft het minimale effect, max factor de maximale effectsterkte.';
  }
  if (label.includes('aandeel niet-westerse')) {
    return 'De minimale factor bepaalt de ondergrens van het effect; de maximale factor bepaalt de bovengrens voor dit sociale risico.';
  }
  if (label.includes('Woningtype')) {
    return 'De minimale factor bepaalt het laagste effect voor woningtype, de maximale factor het hoogste effect.';
  }
  if (label.includes('Bezettingsgraad')) {
    return 'De minimale factor bepaalt de ondergrens van het effect; de maximale factor bepaalt de bovengrens bij hoge bezettingsgraad.';
  }
  if (label.includes('Inkomen')) {
    return 'Arme gebieden krijgen een hoger effect binnen de ingestelde factorrange. Min/max bepalen de onder- en bovengrens.';
  }
  if (label.includes('Stedelijkheidsgraad')) {
    return 'De min/max factor bepaalt de range van stedelijkheidseffecten op de transmissie.';
  }
  if (label.includes('Opleidingsniveau')) {
    return 'De min/max factor bepaalt de onder- en bovengrens van het effect van opleidingsniveau.';
  }
  if (label.includes('RWZI')) {
    return 'De min/max factor bepaalt de range van het effect van RWZI-capaciteit op de transmissie.';
  }
  if (label.includes('Catchment')) {
    return 'De min/max factor bepaalt de range van het effect van catchment-oppervlaktes.';
  }
  if (label.includes('woongebied')) {
    return 'De min/max factor bepaalt de range van het effect voor woongebied.';
  }
  if (label.includes('industrie')) {
    return 'De min/max factor bepaalt de range van het effect voor industriegebied.';
  }
  if (label.includes('agrarisch')) {
    return 'De min/max factor bepaalt de range van het agrarisch effect.';
  }
  if (label.includes('haven')) {
    return 'De min/max factor bepaalt de range van het effect van nabijheid van een haven.';
  }
  return 'Factor beïnvloedt de transmissie op basis van lokale demografie en omgeving.';
}

export function DataFactorRow({ factor, onEnabledChange, onMinFactorChange, onMaxFactorChange }: DataFactorRowProps) {
  return (
    <div className={`grid gap-3 rounded-lg border p-4 transition md:grid-cols-[1fr_86px_320px] ${factor.enabled ? 'border-white/10 bg-black/25 text-white' : 'border-white/5 bg-neutral-900/70 text-gray-500'}`}>
      <div>
        <span className="text-sm">{factor.label}</span>
        <div className="mt-2 text-xs leading-5 text-slate-400">{getFactorDescription(factor.label)}</div>
      </div>
      <label className="flex items-center gap-2 text-xs">
        <input type="checkbox" className="h-4 w-4 accent-white" checked={factor.enabled} onChange={(event) => onEnabledChange(event.target.checked)} />
        {factor.enabled ? 'Aan' : 'Uit'}
      </label>
      <div className="grid gap-3 text-xs">
        <label className="grid gap-1 rounded-xl border border-white/10 bg-slate-950/50 p-3">
          <div className="flex justify-between text-[11px] uppercase tracking-[0.24em] text-slate-400">
            <span>Min factor</span>
            <span>{factor.minFactor.toFixed(1)}×</span>
          </div>
          <input
            disabled={!factor.enabled}
            type="range"
            min="0.1"
            max="2"
            step="0.05"
            value={factor.minFactor}
            onChange={(event) => onMinFactorChange(Number(event.target.value))}
            aria-label={`${factor.label} minimale factor`}
          />
        </label>
        <label className="grid gap-1 rounded-xl border border-white/10 bg-slate-950/50 p-3">
          <div className="flex justify-between text-[11px] uppercase tracking-[0.24em] text-slate-400">
            <span>Max factor</span>
            <span>{factor.maxFactor.toFixed(1)}×</span>
          </div>
          <input
            disabled={!factor.enabled}
            type="range"
            min="0.1"
            max="2"
            step="0.05"
            value={factor.maxFactor}
            onChange={(event) => onMaxFactorChange(Number(event.target.value))}
            aria-label={`${factor.label} maximale factor`}
          />
        </label>
      </div>
    </div>
  );
}
