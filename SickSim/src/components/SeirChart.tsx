export function SeirChart() {
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
