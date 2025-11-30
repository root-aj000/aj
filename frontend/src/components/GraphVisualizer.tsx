// D3 Graph Visualizer Component

'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface GraphNode {
    id: string;
    name: string;
    type: 'function' | 'class' | 'file';
    file?: string;
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
}

interface GraphLink {
    source: string | GraphNode;
    target: string | GraphNode;
    type: 'calls' | 'imports' | 'contains';
}

interface GraphVisualizerProps {
    nodes: GraphNode[];
    links: GraphLink[];
    width?: number;
    height?: number;
    onNodeClick?: (node: GraphNode) => void;
}

export default function GraphVisualizer({
    nodes,
    links,
    width = 800,
    height = 600,
    onNodeClick,
}: GraphVisualizerProps) {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current || nodes.length === 0) return;

        // Clear previous graph
        d3.select(svgRef.current).selectAll('*').remove();

        const svg = d3.select(svgRef.current)
            .attr('width', width)
            .attr('height', height);

        // Create zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                container.attr('transform', event.transform);
            });

        svg.call(zoom as any);

        // Container for graph elements
        const container = svg.append('g');

        // Color scale for node types
        const colorScale = d3.scaleOrdinal<string>()
            .domain(['function', 'class', 'file'])
            .range(['#60a5fa', '#c084fc', '#34d399']);

        // Create force simulation
        const simulation = d3.forceSimulation(nodes as any)
            .force('link', d3.forceLink(links)
                .id((d: any) => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        // Create links
        const link = container.append('g')
            .selectAll('line')
            .data(links)
            .enter()
            .append('line')
            .attr('stroke', '#64748b')
            .attr('stroke-width', 2)
            .attr('stroke-opacity', 0.6)
            .attr('marker-end', 'url(#arrowhead)');

        // Create arrowhead marker
        svg.append('defs')
            .append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#64748b')
            .style('stroke', 'none');

        // Create node groups
        const node = container.append('g')
            .selectAll('g')
            .data(nodes)
            .enter()
            .append('g')
            .attr('cursor', 'pointer')
            .call(d3.drag<any, any>()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended) as any);

        // Add circles to nodes
        node.append('circle')
            .attr('r', 20)
            .attr('fill', (d: GraphNode) => colorScale(d.type))
            .attr('stroke', '#1e293b')
            .attr('stroke-width', 2);

        // Add labels
        node.append('text')
            .text((d: GraphNode) => d.name)
            .attr('x', 0)
            .attr('y', 35)
            .attr('text-anchor', 'middle')
            .attr('fill', '#e2e8f0')
            .attr('font-size', '12px')
            .attr('font-weight', '600');

        // Add tooltips
        node.append('title')
            .text((d: GraphNode) => `${d.name}\nType: ${d.type}${d.file ? `\nFile: ${d.file}` : ''}`);

        // Node click handler
        node.on('click', (event, d: GraphNode) => {
            event.stopPropagation();
            if (onNodeClick) {
                onNodeClick(d);
            }
        });

        // Hover effects
        node.on('mouseenter', function () {
            d3.select(this).select('circle')
                .transition()
                .duration(200)
                .attr('r', 25)
                .attr('stroke-width', 3);
        });

        node.on('mouseleave', function () {
            d3.select(this).select('circle')
                .transition()
                .duration(200)
                .attr('r', 20)
                .attr('stroke-width', 2);
        });

        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', (d: any) => d.source.x)
                .attr('y1', (d: any) => d.source.y)
                .attr('x2', (d: any) => d.target.x)
                .attr('y2', (d: any) => d.target.y);

            node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
        });

        // Drag functions
        function dragstarted(event: any, d: any) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event: any, d: any) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event: any, d: any) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // Cleanup
        return () => {
            simulation.stop();
        };
    }, [nodes, links, width, height, onNodeClick]);

    return (
        <div className="border border-slate-700 rounded-lg overflow-hidden bg-slate-900">
            {/* Controls */}
            <div className="bg-slate-800 border-b border-slate-700 px-4 py-2 flex items-center justify-between">
                <div className="text-sm font-medium text-slate-300">
                    {nodes.length} nodes, {links.length} edges
                </div>
                <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-blue-400"></div>
                        <span className="text-slate-400">Functions</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-purple-400"></div>
                        <span className="text-slate-400">Classes</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-400"></div>
                        <span className="text-slate-400">Files</span>
                    </div>
                </div>
            </div>

            {/* Graph */}
            <svg ref={svgRef} className="w-full h-full"></svg>

            {/* Instructions */}
            <div className="bg-slate-800 border-t border-slate-700 px-4 py-2 text-xs text-slate-400">
                Drag nodes to rearrange • Scroll to zoom • Click nodes for details
            </div>
        </div>
    );
}
