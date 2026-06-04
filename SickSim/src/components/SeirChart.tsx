import React from 'react';
import type { SeirPoint } from '../types';

const series = [
  { key: 'susceptible' as const, label: 'Vatbaar', color: '#38bdf8' },
  { key: 'exposed' as const, label: 'Besmet', color: '#facc15' },
  { key: 'infectious' as const, label: 'Infectieus', color: '#fb7185' },
  { key: 'recovered' as const, label: 'Hersteld', color: '#34d399' },
];

const chartWidth = 540;
const chartHeight = 260;
const leftPadding = 40;
const topPadding = 20;
const bottomPadding = 60;
const svgWidth = 580;

type SeirChartProps = {
  points: SeirPoint[];
  selectedSeries: typeof series[number]['key'];
  onSeriesChange: (selectedSeries: typeof series[number]['key']) => void;
};

export function SeirChart({ points, selectedSeries, onSeriesChange }: SeirChartProps) {
  const chartContainerRef = React.useRef<HTMLDivElement | null>(null);
  const [hoverIndex, setHoverIndex] = React.useState<number | null>(null);
  const [hoverX, setHoverX] = React.useState<number | null>(null);
  const totalPopulation = points[0]
    ? points[0].susceptible + points[0].exposed + points[0].infectious + points[0].recovered
    : 1;

  const getPercent = (value: number) => (totalPopulation === 0 ? 0 : (value / totalPopulation) * 100);
  const xPosition = (index: number) => leftPadding + (index / Math.max(points.length - 1, 1)) * chartWidth;
  const yPosition = (percent: number) => topPadding + ((100 - percent) / 100) * chartHeight;
  const tooltipWidth = 240;
  const containerWidth = chartContainerRef.current?.clientWidth ?? svgWidth;
  const tooltipLeft = hoverX !== null
    ? Math.min(Math.max(hoverX + 10, 8), containerWidth - tooltipWidth - 8)
    : 8;
  const tickCount = Math.max(2, Math.min(7, Math.floor(points.length / 8)));
  const tickIndexes = Array.from({ length: tickCount + 1 }, (_, i) => Math.round(i * (points.length - 1) / tickCount));

  const buildPath = (key: keyof Omit<SeirPoint, 'day'>) => points
    .map((point, index) => {
      const x = xPosition(index);
      const y = yPosition(getPercent(point[key]));
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');

  const paths = series.map((item) => ({ ...item, path: buildPath(item.key) }));
  const hoveredPoint = hoverIndex !== null ? points[hoverIndex] : points[points.length - 1];

  const handleMouseMove = (event: React.MouseEvent<SVGRectElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = event.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, relativeX / rect.width));
    const maxIndex = Math.max(points.length - 1, 1);
    const index = Math.round(ratio * maxIndex);
    const clampedIndex = Math.max(0, Math.min(points.length - 1, index));
    setHoverIndex(clampedIndex);

    const x = xPosition(clampedIndex);
    setHoverX(Math.max(leftPadding, Math.min(leftPadding + chartWidth, x)));
  };

  const activeSeries = series.find((item) => item.key === selectedSeries) ?? series[2];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm text-gray-400">SEIR percentage over tijd</div>
          <h2 className="text-2xl font-semibold text-white">Procentuele simulatie</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {series.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onSeriesChange(item.key)}
              className={`rounded-full border px-3 py-2 text-sm font-medium transition ${selectedSeries === item.key ? 'border-white bg-white/10 text-white' : 'border-white/10 text-gray-300 hover:border-white/20 hover:text-white'}`}
              style={{ boxShadow: selectedSeries === item.key ? `0 0 0 1px ${item.color}` : undefined }}
            >
              <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div ref={chartContainerRef} className="relative overflow-hidden rounded-3xl border border-white/10 bg-black/30 p-4">
        <svg viewBox="0 0 580 360" className="h-[360px] w-full">
          {[0, 25, 50, 75, 100].map((percent) => {
            const y = yPosition(percent);
            return (
              <g key={percent}>
                <line x1={leftPadding} x2={leftPadding + chartWidth} y1={y} y2={y} stroke="rgba(255,255,255,0.1)" />
                <text x={8} y={y + 4} fill="rgba(255,255,255,0.6)" fontSize="11">{percent}%</text>
              </g>
            );
          })}

          <line x1={leftPadding} x2={leftPadding} y1={topPadding} y2={topPadding + chartHeight} stroke="rgba(255,255,255,0.24)" />
          <line x1={leftPadding} x2={leftPadding + chartWidth} y1={topPadding + chartHeight} y2={topPadding + chartHeight} stroke="rgba(255,255,255,0.24)" />

          {paths.map((item) => (
            <path
              key={item.key}
              d={item.path}
              fill="none"
              stroke={item.color}
              strokeWidth={selectedSeries === item.key ? 3.2 : 2}
              opacity={selectedSeries === item.key ? 1 : 0.42}
            />
          ))}

          {tickIndexes.map((index) => {
            const x = xPosition(index);
            return (
              <g key={index}>
                <line x1={x} x2={x} y1={topPadding + chartHeight} y2={topPadding + chartHeight + 6} stroke="rgba(255,255,255,0.35)" />
                <text x={x} y={topPadding + chartHeight + 20} fill="rgba(255,255,255,0.6)" fontSize="11" textAnchor="middle">Dag {points[index].day}</text>
              </g>
            );
          })}

          {hoverIndex !== null && hoverX !== null && (
            <g>
              <line x1={hoverX} x2={hoverX} y1={topPadding} y2={topPadding + chartHeight} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
              {series.map((item) => {
                const point = points[hoverIndex][item.key];
                const y = yPosition(getPercent(point));
                return (
                  <circle key={item.key} cx={xPosition(hoverIndex)} cy={y} r={selectedSeries === item.key ? 5.5 : 4} fill={item.color} stroke="rgba(255,255,255,0.18)" />
                );
              })}
            </g>
          )}

          <rect
            x={leftPadding}
            y={topPadding}
            width={chartWidth}
            height={chartHeight}
            fill="transparent"
            onMouseMove={handleMouseMove}
            onMouseLeave={() => {
              setHoverIndex(null);
              setHoverX(null);
            }}
          />
        </svg>

        {hoverIndex !== null && hoveredPoint && (
          <div className="pointer-events-none absolute top-6" style={{ left: tooltipLeft }}>
            <div className="rounded-2xl border border-white/10 bg-slate-950/95 p-4 text-sm text-white shadow-xl shadow-black/30" style={{ width: tooltipWidth }}>
              <div className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-400">Dag {hoveredPoint.day}</div>
              {series.map((item) => {
                const value = hoveredPoint[item.key];
                const percent = getPercent(value);
                return (
                  <div key={item.key} className="flex items-center justify-between gap-4 text-[13px] leading-5">
                    <span className="flex items-center gap-2 text-slate-200">
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      {item.label}
                    </span>
                    <span className="font-semibold text-white">{percent.toFixed(1)}% ({value.toLocaleString('nl-NL')})</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-3 rounded-3xl border border-white/10 bg-black/20 p-5 text-sm text-slate-300">
        <div>
          <div className="mb-1 text-xs uppercase tracking-[0.24em] text-slate-500">Geselecteerde lijn</div>
          <div className="text-base font-semibold text-white">{activeSeries.label}</div>
          <div className="text-sm text-slate-400">{activeSeries.key === 'susceptible' ? 'Sociaal gezien nog vatbare groep.' : activeSeries.key === 'exposed' ? 'Besmet, maar nog niet besmettelijk.' : activeSeries.key === 'infectious' ? 'Actief besmettelijke personen.' : 'Hersteld en niet meer vatbaar.'}</div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
            <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Laatste dag</div>
            <div className="mt-2 text-lg font-semibold text-white">{points[points.length - 1][selectedSeries].toLocaleString('nl-NL')}</div>
            <div className="text-xs text-slate-400">personen ({getPercent(points[points.length - 1][selectedSeries]).toFixed(1)}%)</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
            <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Bevolking</div>
            <div className="mt-2 text-lg font-semibold text-white">{totalPopulation.toLocaleString('nl-NL')}</div>
            <div className="text-xs text-slate-400">*constante populatie</div>
          </div>
        </div>
      </div>
    </div>
  );
}
