import type { SeirPoint } from '../types';

export function SeirChart({ points }: { points: SeirPoint[] }) {
  const labels = ['Vatbaar', 'Besmet', 'Infectieus', 'Hersteld'];
  const maxValue = Math.max(1, ...points.flatMap((point) => [point.susceptible, point.exposed, point.infectious, point.recovered]));
  const buildPath = (key: keyof Omit<SeirPoint, 'day'>) => points.map((point, index) => {
    const x = 20 + (index / Math.max(points.length - 1, 1)) * 540;
    const y = 310 - (point[key] / maxValue) * 250;
    return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');
  const paths = [
    buildPath('susceptible'),
    buildPath('exposed'),
    buildPath('infectious'),
    buildPath('recovered'),
  ];

  return (
    <svg viewBox="0 0 580 360" className="h-[360px] w-full rounded-lg border border-white/10 bg-black/35">
      {[80, 150, 220, 290].map((y) => <line key={y} x1="20" x2="560" y1={y} y2={y} stroke="rgba(255,255,255,0.1)" />)}
      {paths.map((path, index) => <path key={path} d={path} fill="none" stroke="white" strokeWidth={index === 0 ? 3 : 2} opacity={1 - index * 0.18} />)}
      {labels.map((label, index) => <text key={label} x={28 + index * 126} y="335" fill="rgba(255,255,255,0.72)" fontSize="13">{label}</text>)}
    </svg>
  );
}
