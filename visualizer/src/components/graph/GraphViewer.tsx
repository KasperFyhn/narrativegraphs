import React, { useEffect, useMemo, useState } from 'react';
import Graph, { GraphEvents } from 'react-vis-graph-wrapper';
import { Edge, GraphData, Node } from '../../types/graph';
import { NodeInfo } from '../inspector/info/NodeInfo';
import { EdgeInfo } from '../inspector/info/EdgeInfo';
import { useServiceContext } from '../../contexts/ServiceContext';
import { useGraphQuery } from '../../hooks/useGraphQuery';
import { useGraphOptionsContext } from '../../contexts/GraphOptionsContext';
import { SideBar } from './SideBar';

export const GraphViewer: React.FC = () => {
  const { graphService } = useServiceContext();

  const { query, filter, toggleFocusEntityId, addBlacklistedEntityId } =
    useGraphQuery();

  const { options } = useGraphOptionsContext();

  const [selectedNode, setSelectedNode] = useState<Node>();
  const [selectedEdge, setSelectedEdge] = useState<Edge>();

  const [graphData, setGraphData] = useState<GraphData>({
    edges: [],
    nodes: [],
  });
  useEffect(() => {
    graphService.getGraph(query, filter).then((r) => setGraphData(r));
  }, [graphService, filter, query]);

  const coloredGraphData = useMemo(() => {
    const colorNode = (n: Node): string => {
      if (query.focusEntities?.includes(n.id.toString())) {
        return 'lightgreen';
      } else if (filter.blacklistedEntityIds?.includes(n.id.toString())) {
        return 'red';
      } else {
        return 'cyan';
      }
    };
    return {
      edges: graphData.edges.map((e) => ({
        ...e,
        width: Math.log10(e.totalFrequency || 10),
        arrows: query.connectionType == 'cooccurrence' ? '' : undefined,
      })),
      nodes: graphData.nodes.map((n) => ({
        ...n,
        color: colorNode(n),
      })),
    };
  }, [
    graphData.edges,
    graphData.nodes,
    query.focusEntities,
    query.connectionType,
    filter.blacklistedEntityIds,
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
      toggleFocusEntityId(node);
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
      <div style={{ height: '100vh' }}>
        {selectedNode && <NodeInfo node={selectedNode} />}
        {selectedEdge && <EdgeInfo edge={selectedEdge} />}
        <Graph graph={coloredGraphData} events={events} options={options} />
      </div>
      <SideBar />
    </div>
  );
};
