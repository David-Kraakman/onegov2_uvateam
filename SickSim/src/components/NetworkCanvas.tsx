import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { NetworkData, AgentProfile, DataFactor } from '../types';

type NetworkCanvasProps = {
  network: NetworkData | null;
  selectedNodeId?: string;
  onNodeSelect: (id: string | null) => void;
  dataFactors: DataFactor[]; // Nieuw: Ontvang de live instellingen!
};

type RiskCategory = 'low' | 'medium' | 'high';

// Wiskundige helper: Schaal een waarde naar de door de dokter ingestelde min/max
function mapDynamicRisk(val: number, domainMin: number, domainMax: number, targetMin: number, targetMax: number, invert = false): number {
  let ratio = (val - domainMin) / (domainMax - domainMin);
  ratio = Math.max(0, Math.min(1, ratio)); // Begrens tussen 0 en 1
  if (invert) ratio = 1 - ratio; 
  return targetMin + (ratio * (targetMax - targetMin));
}

function getRiskCategory(score: number): RiskCategory {
  if (score < 1.05) return 'low';
  if (score < 1.25) return 'medium';
  return 'high';
}

export function NetworkCanvas({ network, selectedNodeId, onNodeSelect, dataFactors }: NetworkCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 0.8 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedRiskCategory, setSelectedRiskCategory] = useState<RiskCategory | null>(null);

  // --- De Dynamische Risico Calculator ---
  const calculateRiskScore = useCallback((p: AgentProfile) => {
    let totalRisk = 0;
    let activeFactorsCount = 0;

    // Helper om snel een factor te vinden op basis van een woord in de label
    const getFactor = (keyword: string) => dataFactors.find(f => f.label.toLowerCase().includes(keyword.toLowerCase()));

    const fBevolking = getFactor('bevolkingsomvang');
    if (fBevolking?.enabled) {
      totalRisk += mapDynamicRisk(p.bevolkingsomvang, 800, 14000, fBevolking.minFactor, fBevolking.maxFactor);
      activeFactorsCount++;
    }

    const fBezettingsgraad = getFactor('bezettingsgraad');
    if (fBezettingsgraad?.enabled) {
      totalRisk += mapDynamicRisk(p.bezettingsgraadWoning, 1.2, 3.6, fBezettingsgraad.minFactor, fBezettingsgraad.maxFactor);
      activeFactorsCount++;
    }

    const fInkomen = getFactor('inkomen');
    if (fInkomen?.enabled) {
      totalRisk += mapDynamicRisk(p.gemiddeldBestedbaarInkomen, 24000, 68000, fInkomen.minFactor, fInkomen.maxFactor, true);
      activeFactorsCount++;
    }

    const fStedelijkheid = getFactor('stedelijkheidsgraad');
    if (fStedelijkheid?.enabled) {
      totalRisk += mapDynamicRisk(p.stedelijkheidsgraad, 1, 5, fStedelijkheid.minFactor, fStedelijkheid.maxFactor, true);
      activeFactorsCount++;
    }

    const fNietWesters = getFactor('niet-westerse');
    if (fNietWesters?.enabled) {
      totalRisk += mapDynamicRisk(p.aandeelNietWesterseAchtergrond, 0, 50, fNietWesters.minFactor, fNietWesters.maxFactor);
      activeFactorsCount++;
    }

    const fLeeftijd = getFactor('leeftijdsverdeling');
    if (fLeeftijd?.enabled) {
      const kwetsbaarPercentage = p.leeftijdsverdeling['65+'] + p.leeftijdsverdeling['0-14'];
      totalRisk += mapDynamicRisk(kwetsbaarPercentage, 10, 50, fLeeftijd.minFactor, fLeeftijd.maxFactor);
      activeFactorsCount++;
    }

    const fOpleiding = getFactor('opleidingsniveau');
    if (fOpleiding?.enabled) {
      totalRisk += mapDynamicRisk(p.opleidingsniveau.laag, 10, 40, fOpleiding.minFactor, fOpleiding.maxFactor);
      activeFactorsCount++;
    }

    const fWoningtype = getFactor('woningtype');
    if (fWoningtype?.enabled) {
      const typeFactor = p.woningtype === 'appartement' ? fWoningtype.maxFactor 
                       : (p.woningtype === 'rijtjeshuis' ? (fWoningtype.minFactor + fWoningtype.maxFactor)/2 
                       : fWoningtype.minFactor);
      totalRisk += typeFactor;
      activeFactorsCount++;
    }

    // Als er geen enkele factor aan staat, is het risico standaard 1.0 (neutraal)
    if (activeFactorsCount === 0) return 1.0;

    // Neem het gemiddelde van alle actieve factoren
    return totalRisk / activeFactorsCount;
  }, [dataFactors]);

  useEffect(() => {
    if (network) setTransform({ x: 100, y: 50, k: 0.8 });
  }, [network]);

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault(); 
    const scaleFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setTransform((prev) => {
      const newScale = Math.min(Math.max(prev.k * scaleFactor, 0.2), 5);
      return { ...prev, k: newScale };
    });
  }, []);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (svgEl) {
      svgEl.addEventListener('wheel', handleWheel, { passive: false });
      return () => svgEl.removeEventListener('wheel', handleWheel);
    }
  }, [handleWheel]);

  if (!network) {
    return (
      <div className="flex h-[500px] w-full items-center justify-center rounded-xl border border-white/10 bg-black/20">
        <p className="text-gray-400">Genereer een netwerk om de visualisatie te starten.</p>
      </div>
    );
  }

  const handlePointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    if ((e.target as SVGElement).tagName === 'circle') return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
  };

  const handlePointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!isDragging) return;
    setTransform((prev) => ({ ...prev, x: e.clientX - dragStart.x, y: e.clientY - dragStart.y }));
  };

  const handlePointerUp = () => setIsDragging(false);

  const connectedNodeIds = new Set<string>();
  if (selectedNodeId) {
    connectedNodeIds.add(selectedNodeId);
    network.edges.forEach((edge) => {
      if (edge.source === selectedNodeId) connectedNodeIds.add(edge.target);
      if (edge.target === selectedNodeId) connectedNodeIds.add(edge.source);
    });
  }

  const showLabels = transform.k > 1.8;

  const toggleRiskCategory = (category: RiskCategory) => {
    setSelectedRiskCategory(prev => prev === category ? null : category);
    onNodeSelect(null);
  };

  return (
    <div 
      className="relative h-[500px] w-full overflow-hidden rounded-xl border border-white/10 bg-black/20 cursor-grab active:cursor-grabbing"
      style={{ touchAction: 'none' }} 
    >
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        onClick={(e) => {
          if ((e.target as SVGElement).tagName === 'svg') {
            onNodeSelect(null);
            setSelectedRiskCategory(null);
          }
        }}
      >
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
          {network.edges.map((edge) => {
            const sourceNode = network.nodes.find((n) => n.id === edge.source);
            const targetNode = network.nodes.find((n) => n.id === edge.target);
            if (!sourceNode || !targetNode) return null;

            const isHighlightedByNode = selectedNodeId && (edge.source === selectedNodeId || edge.target === selectedNodeId);
            const isFadedByNode = selectedNodeId && !isHighlightedByNode;
            const isFadedByCategory = selectedRiskCategory !== null;

            return (
              <line
                key={`${edge.source}-${edge.target}`}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={isHighlightedByNode ? '#ffffff' : '#9ca3af'}
                strokeWidth={isHighlightedByNode ? 2 / transform.k : 0.5 / transform.k}
                strokeOpacity={isFadedByNode || isFadedByCategory ? 0.05 : isHighlightedByNode ? 0.9 : 0.15}
                className="transition-all duration-300"
              />
            );
          })}

          {network.nodes.map((node) => {
            // HIER WORDT DE LIVE DATA GEBRUIKT!
            const riskScore = node.profile ? calculateRiskScore(node.profile) : 1.0;
            const riskCategory = getRiskCategory(riskScore);

            const isSelectedNode = node.id === selectedNodeId;
            const isConnectedToSelected = connectedNodeIds.has(node.id);
            
            let isFaded = false;
            if (selectedNodeId) {
              isFaded = !isConnectedToSelected;
            } else if (selectedRiskCategory) {
              isFaded = riskCategory !== selectedRiskCategory;
            }

            const fillClass = riskCategory === 'high' ? 'fill-red-500' 
              : riskCategory === 'medium' ? 'fill-amber-500'
              : 'fill-emerald-500';

            return (
              <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                <circle
                  r={isSelectedNode ? 6 / transform.k : 4 / transform.k}
                  className={`
                    cursor-pointer transition-all duration-300
                    ${isFaded ? 'fill-gray-600 opacity-15' : fillClass}
                    ${isSelectedNode ? 'stroke-white' : ''}
                  `}
                  strokeWidth={isSelectedNode ? 2 / transform.k : 0}
                  onClick={(e) => {
                    e.stopPropagation();
                    onNodeSelect(node.id);
                    setSelectedRiskCategory(null);
                  }}
                />
                
                {showLabels && !isFaded && (
                  <text
                    y={(10 / transform.k)}
                    className="pointer-events-none fill-white font-medium opacity-80"
                    textAnchor="middle"
                    style={{ fontSize: `${8 / transform.k}px` }}
                  >
                    {node.label}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
      
      {/* Legenda */}
      <div className="absolute top-3 left-3 rounded-lg border border-white/10 bg-black/60 p-3 text-xs backdrop-blur-md">
        <div className="mb-2 font-semibold text-white">Transmissie Risico</div>
        <div className="flex flex-col gap-2">
          <button onClick={() => toggleRiskCategory('high')} className={`flex items-center gap-2 hover:bg-white/10 p-1 rounded transition-colors ${selectedRiskCategory === 'high' ? 'bg-white/20 ring-1 ring-white/30' : ''}`}>
            <div className="h-3 w-3 rounded-full bg-red-500"></div><span className="text-gray-300">Hoog ({">"} 1.25x)</span>
          </button>
          <button onClick={() => toggleRiskCategory('medium')} className={`flex items-center gap-2 hover:bg-white/10 p-1 rounded transition-colors ${selectedRiskCategory === 'medium' ? 'bg-white/20 ring-1 ring-white/30' : ''}`}>
            <div className="h-3 w-3 rounded-full bg-amber-500"></div><span className="text-gray-300">Gemiddeld</span>
          </button>
          <button onClick={() => toggleRiskCategory('low')} className={`flex items-center gap-2 hover:bg-white/10 p-1 rounded transition-colors ${selectedRiskCategory === 'low' ? 'bg-white/20 ring-1 ring-white/30' : ''}`}>
            <div className="h-3 w-3 rounded-full bg-emerald-500"></div><span className="text-gray-300">Laag ({"<"} 1.05x)</span>
          </button>
        </div>
      </div>
    </div>
  );
}