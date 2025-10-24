import React, { useEffect, useMemo, useState } from 'react';
import Graph, { GraphEvents } from 'react-vis-graph-wrapper';
import { Edge, GraphData, Node } from '../../types/graph';
import { NodeInfo } from '../inspector/NodeInfo';
import { EdgeInfo } from '../inspector/EdgeInfo';
import { useServiceContext } from '../../contexts/ServiceContext';
import { useGraphFilter } from '../../hooks/useGraphFilter';
import { useGraphOptionsContext } from '../../contexts/GraphOptionsContext';
import { SideBar } from './SideBar';

export const GraphViewer: React.FC = () => {
  const { graphService } = useServiceContext();

  const { filter, toggleWhitelistedEntityId, addBlacklistedEntityId } =
    useGraphFilter();

  const { options } = useGraphOptionsContext();

  const [selectedNode, setSelectedNode] = useState<Node>();
  const [selectedEdge, setSelectedEdge] = useState<Edge>();

  const [graphData, setGraphData] = useState<GraphData>({
    edges: [],
    nodes: [],
  });
  useEffect(() => {
    graphService.getGraph(filter).then((r) => setGraphData(r));
  }, [graphService, filter]);

  const coloredGraphData = useMemo(() => {
    const colorNode = (n: Node): string => {
      if (filter.whitelistedEntityIds?.includes(n.id.toString())) {
        return 'lightgreen';
      } else if (n.focus) {
        return 'yellow';
      } else if (!filter.blacklistedEntityIds?.includes(n.id.toString())) {
        return 'cyan';
      } else {
        return 'red';
      }
    };
    return {
      edges: graphData.edges.map((e) => ({
        ...e,
        width: Math.log10(e.totalFrequency || 10),
      })),
      nodes: graphData.nodes.map((n) => ({
        ...n,
        color: colorNode(n),
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
      nodesMap: new Map(graphData.nodes.map((node) => [node.id, node])),
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
      addBlacklistedEntityId(...nodes.map((v: number) => v.toString()));
    },
    selectNode: ({ nodes }) => {
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

  return (
    <div>
      <div className="graph-container">
        {selectedNode && <NodeInfo node={selectedNode} />}
        {selectedEdge && <EdgeInfo edge={selectedEdge} />}
        <Graph graph={coloredGraphData} events={events} options={options} />
      </div>
      <SideBar />
    </div>
  );
};
