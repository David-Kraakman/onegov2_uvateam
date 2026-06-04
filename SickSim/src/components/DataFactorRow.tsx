import type { DataFactor } from '../types';

type DataFactorRowProps = {
  factor: DataFactor;
  onEnabledChange: (enabled: boolean) => void;
  onWeightChange: (weight: number) => void;
};

export function DataFactorRow({ factor, onEnabledChange, onWeightChange }: DataFactorRowProps) {
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
