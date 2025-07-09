import React, { useEffect, useMemo, useState } from 'react';
import Graph, { GraphEvents, Options } from 'react-vis-graph-wrapper';
import { GraphOptionsControlPanel } from './GraphOptionsControlPanel';
import { Edge, GraphData, Node } from '../../types/graph';
import { NodeInfo } from '../inspector/NodeInfo';
import { EdgeInfo } from '../inspector/EdgeInfo';
import { useServiceContext } from '../../contexts/ServiceContext';
import { useGraphFilter } from '../../hooks/useGraphFilter';
import { GraphFilterControlPanel } from './FilterControlPanel/GraphFilterControlPanel';

export const GraphViewer: React.FC = () => {
  const { graphService } = useServiceContext();

  const [selectedNode, setSelectedNode] = useState<Node>();
  const [selectedEdge, setSelectedEdge] = useState<Edge>();

  const { filter, toggleWhitelistedEntityId, addBlacklistedEntityId } =
    useGraphFilter();

  const [graphData, setGraphData] = useState<GraphData>({
    edges: [],
    nodes: [],
  });
  useEffect(() => {
    graphService.getGraph(filter).then((r) => setGraphData(r));
  }, [graphService, filter]);

  const coloredGraphData = useMemo(() => {
    return {
      edges: graphData.edges.map((e) => ({
        ...e,
        width: Math.log10(e.totalTermFrequency || 10),
      })),
      nodes: graphData.nodes.map((n) => ({
        ...n,
        // TODO: fix this horrible block
        color: filter.whitelistedEntityIds?.includes(n.id.toString())
          ? 'lightgreen'
          : n.focus
            ? 'yellow'
            : filter.blacklistedEntityIds?.includes(n.id.toString())
              ? 'red'
              : 'cyan',
      })),
    };
  }, [
    filter.blacklistedEntityIds,
    filter.whitelistedEntityIds,
    graphData.edges,
    graphData.nodes,
  ]);

  const graphDataMaps = useMemo(() => {
    return {
      nodesMap: new Map(graphData.nodes.map((node) => [node.id!, node])),
      edgeGroupMap: new Map(graphData.edges.map((edge) => [edge.id, edge])),
    };
  }, [graphData]);

  const events: GraphEvents = {
    doubleClick: ({ nodes }) => {
      if (nodes.length === 0) return;
      const node: string = nodes.map((v: number) => v.toString())[0];
      toggleWhitelistedEntityId(node);
    },
    hold: ({ nodes }) => {
      if (nodes.length === 0) return;
      const node: string = nodes.map((v: number) => v.toString())[0];
      addBlacklistedEntityId(node);
    },
    select: ({ nodes }) => {
      if (nodes.length < 2) return;
      nodes.forEach((v: number) => addBlacklistedEntityId(v.toString()));
    },
    selectNode: ({ nodes, edges }) => {
      setSelectedEdge(undefined);
      setSelectedNode(graphDataMaps.nodesMap.get(nodes[0]));
    },
    selectEdge: ({ nodes, edges }) => {
      if (nodes.length < 1) {
        setSelectedNode(undefined);
        setSelectedEdge(graphDataMaps.edgeGroupMap.get(edges[0]));
      }
    },
    deselectNode: () => {
      setSelectedNode(undefined);
    },
    deselectEdge: () => {
      setSelectedEdge(undefined);
    },
  };

  const [options, setOptions] = useState<Options>({
    physics: {
      enabled: true,
      barnesHut: {
        springLength: 300,
      },
    },
    edges: {
      smooth: true,
      font: {
        align: 'top',
      },
    },
  });

  const [showControlPanel, setShowControlPanel] = useState<boolean>(true);

  return (
    <div>
      <button
        onClick={() => setShowControlPanel((prev) => !prev)}
        style={{
          position: 'absolute',
          top: '1px',
          right: '1px',
          zIndex: 5,
          fontSize: '16px',
        }}
      >
        {showControlPanel ? <>&#8614;</> : <>&#8612;</>}
      </button>
      <div
        className={
          'panel control-panel ' +
          (showControlPanel ? '' : 'control-panel--hidden')
        }
      >
        <GraphOptionsControlPanel options={options} setOptions={setOptions} />
        <hr />
        <GraphFilterControlPanel />
      </div>

      <div className="graph-container">
        {selectedNode && <NodeInfo node={selectedNode} />}
        {selectedEdge && <EdgeInfo edge={selectedEdge} />}
        <Graph graph={coloredGraphData} options={options} events={events} />
      </div>
    </div>
  );
};
