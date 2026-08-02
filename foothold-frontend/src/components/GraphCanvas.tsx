import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { GraphData, ConceptNode } from '../types';

interface GraphCanvasProps {
  data: GraphData;
}

export default function GraphCanvas({ data }: GraphCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || data.nodes.length === 0) return;

    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('viewBox', [0, 0, width, height])
      .style('cursor', 'grab');

    // Arrow markers
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 28) // Pushed further out for arcs
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#9ca3af')
      .style('stroke', 'none');

    const g = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    svg.call(zoom as any);

    const nodes = data.nodes.map(d => ({ ...d })) as (ConceptNode & d3.SimulationNodeDatum)[];
    const links = data.edges.map(d => ({ ...d, source: d.source_id, target: d.target_id })) as any;

    // STRONGER PHYSICS ENGINE
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(350)) // Massive distance increase
      .force('charge', d3.forceManyBody().strength(-1500)) // Massive repulsion increase
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(100)); // Larger collision boundary

    // Draw Edges as Paths (Arcs) to prevent overlap
    const link = g.append('g')
      .selectAll('path')
      .data(links)
      .join('path')
      .attr('stroke', '#cbd5e1')
      .attr('stroke-width', 2)
      .attr('fill', 'none')
      .attr('marker-end', 'url(#arrowhead)');

    // Edge Labels with text halos for legibility
    const edgeLabels = g.append('g')
      .selectAll('text')
      .data(links)
      .join('text')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', '#64748b')
      .attr('text-anchor', 'middle')
      .attr('paint-order', 'stroke')
      .attr('stroke', '#f8fafc') // Matches background color
      .attr('stroke-width', 5) // Creates a halo cutting through lines
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round')
      .text((d: any) => d.relationship.replace(/_/g, ' '));

    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any)
      .on('dblclick', dblclicked);

    node.append('circle')
      .attr('r', 18)
      .attr('fill', '#3b82f6')
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 4)
      .style('filter', 'drop-shadow(0px 4px 6px rgba(0, 0, 0, 0.1))');

    // Node Labels with text halos
    node.append('text')
      .attr('dy', 35)
      .attr('text-anchor', 'middle')
      .attr('font-size', '13px')
      .attr('font-weight', '600')
      .attr('fill', '#1e293b')
      .attr('paint-order', 'stroke')
      .attr('stroke', '#f8fafc')
      .attr('stroke-width', 5)
      .text((d: any) => d.name);

    simulation.on('tick', () => {
      // Calculate curved paths
      link.attr('d', (d: any) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const dr = Math.sqrt(dx * dx + dy * dy) * 1.5; // Controls curve strictness
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
      });

      // Position edge label along the curve
      edgeLabels
        .attr('x', (d: any) => {
          const dy = d.target.y - d.source.y;
          // Offset slightly from center to account for curve
          return (d.source.x + d.target.x) / 2 + (dy * 0.15); 
        })
        .attr('y', (d: any) => {
          const dx = d.target.x - d.source.x;
          return (d.source.y + d.target.y) / 2 - (dx * 0.15);
        });

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }
    function dragended(event: any, _d: any) {
      if (!event.active) simulation.alphaTarget(0);
    }
    function dblclicked(_event: any, d: any) {
      d.fx = null;
      d.fy = null;
      simulation.alphaTarget(0.3).restart();
    }

    return () => {
      simulation.stop();
    };
  }, [data]);

  return (
    <div className="w-full h-full bg-[#f8fafc] relative overflow-hidden">
      <svg ref={svgRef} className="w-full h-full absolute inset-0" />
      <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm px-3 py-1.5 rounded-md border border-gray-200 text-xs text-gray-500 shadow-sm pointer-events-none">
        Drag to pin • Double-click to unpin • Scroll to zoom
      </div>
    </div>
  );
}