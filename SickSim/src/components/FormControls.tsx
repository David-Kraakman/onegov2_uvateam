import React from 'react';

export function AnimatedTitle({ text }: { text: string }) {
  return (
    <h1 className="mb-6 shrink-0 text-4xl font-normal tracking-tight md:text-5xl lg:text-6xl" style={{ letterSpacing: '-0.04em' }}>
      {text.split('').map((char, index) => (
        <span className="inline-block animate-letter" style={{ animationDelay: `${index * 45}ms` }} key={`${char}-${index}`}>{char === ' ' ? '\u00a0' : char}</span>
      ))}
    </h1>
  );
}

export function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return <h2 className="mb-4 mt-8 flex items-center gap-2 text-xl font-medium first:mt-0">{icon}{title}</h2>;
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block rounded-lg border border-white/10 bg-black/25 p-4">
      <span className="mb-2 block text-sm font-medium">{label}</span>
      {children}
      {hint && <span className="mt-2 block text-xs leading-5 text-gray-300">{hint}</span>}
    </label>
  );
}

type RangeProps = {
  label: string;
  hint?: string;
  min: number;
  max: number;
  step: number;
  initialValue: number;
  suffix?: string;
  decimals?: number;
  onValueChange?: (value: number) => void;
};

export function Range({ label, hint, min, max, step, initialValue, suffix = '', decimals, onValueChange }: RangeProps) {
  const [value, setValue] = React.useState(initialValue);
  const displayValue = decimals === undefined ? String(value) : value.toFixed(decimals);
  const updateValue = (nextValue: number) => {
    setValue(nextValue);
    onValueChange?.(nextValue);
  };

  return (
    <Field label={label} hint={hint}>
      <div className="grid gap-2">
        <div className="flex justify-between text-xs text-gray-300">
          <span>{min}{suffix}</span>
          <span className="rounded bg-white px-2 py-1 font-medium text-black">{displayValue}{suffix}</span>
          <span>{max}{suffix}</span>
        </div>
        <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => updateValue(Number(event.target.value))} />
      </div>
    </Field>
  );
}
