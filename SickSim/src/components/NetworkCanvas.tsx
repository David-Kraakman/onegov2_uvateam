export function NetworkCanvas() {
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
