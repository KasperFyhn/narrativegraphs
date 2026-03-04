import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import Graph, { GraphEvents } from 'react-vis-graph-wrapper';
import { Network } from 'vis-network';
import { Edge, GraphData, Node } from '../../types/graph';
import { NodeInfo } from '../inspector/info/NodeInfo';
import { EdgeInfo } from '../inspector/info/EdgeInfo';
import { useServiceContext } from '../../contexts/ServiceContext';
import { useGraphQuery } from '../../hooks/useGraphQuery';
import {
  layoutPrecisionToParams,
  useGraphOptionsContext,
} from '../../contexts/GraphOptionsContext';
import { useSelectionContext } from '../../contexts/SelectionContext';
import { SideBar } from './SideBar';
import { Box, Progress, Stack, Text } from '@mantine/core';

export const GraphViewer: React.FC = () => {
  const { graphService } = useServiceContext();

  const { query, filter, toggleFocusEntityId, addBlacklistedEntityId } =
    useGraphQuery();

  const { options, layoutPrecision } = useGraphOptionsContext();
  const layoutPrecisionRef = useRef(layoutPrecision);
  useEffect(() => {
    layoutPrecisionRef.current = layoutPrecision;
  }, [layoutPrecision]);
  const { setHasSelection, getEntityColor } = useSelectionContext();

  const [selectedNode, setSelectedNode] = useState<Node>();
  const [selectedEdge, setSelectedEdge] = useState<Edge>();
  const [isStabilizing, setIsStabilizing] = useState(false);
  const [stabilizationProgress, setStabilizationProgress] = useState(0);

  // Ref so the stabilizationIterationsDone handler always reads the latest value
  // without needing to re-register the listener when the toggle changes.
  const physicsEnabledRef = useRef(options.physics?.enabled ?? false);
  useEffect(() => {
    physicsEnabledRef.current = options.physics?.enabled ?? false;
  }, [options.physics?.enabled]);

  const networkRef = useRef<Network | null>(null);

  // Called once by react-vis-graph-wrapper after the vis-network instance is created.
  const handleGetNetwork = useCallback((network: Network) => {
    networkRef.current = network;

    network.on('stabilizationProgress', (params) => {
      const { iterations, total } = params as {
        iterations: number;
        total: number;
      };
      setStabilizationProgress(Math.round((iterations / total) * 100));
    });

    // After background layout finishes, restore physics to the user's preference.
    network.on('stabilizationIterationsDone', () => {
      network.setOptions({ physics: { enabled: physicsEnabledRef.current } });
      setIsStabilizing(false);
      setStabilizationProgress(0);
    });
  }, []);

  useEffect(() => {
    setHasSelection(selectedNode !== undefined || selectedEdge !== undefined);
  }, [selectedNode, selectedEdge, setHasSelection]);

  const [graphData, setGraphData] = useState<GraphData>({
    edges: [],
    nodes: [],
  });
  useEffect(() => {
    graphService.getGraph(query, filter).then((r) => setGraphData(r));
  }, [graphService, filter, query]);

  // When graph data changes in layout mode, run background stabilization to
  // recompute positions without rendering intermediate frames.
  // When physics is ON, vis-network's live physics handles data changes naturally.
  useEffect(() => {
    const network = networkRef.current;
    if (!network || graphData.nodes.length === 0 || physicsEnabledRef.current)
      return;

    const { iterations, minVelocity } = layoutPrecisionToParams(
      layoutPrecisionRef.current,
    );
    // fit: false preserves the current viewport after stabilization.
    network.setOptions({
      physics: {
        enabled: true,
        minVelocity,
        stabilization: { enabled: false, fit: false },
      },
    });
    network.stabilize(iterations);
    setIsStabilizing(true);
    setStabilizationProgress(0);
  }, [graphData]);

  const coloredGraphData = useMemo(() => {
    return {
      edges: graphData.edges.map((e) => ({
        ...e,
        width: Math.log10(e.totalFrequency || 10),
        arrows: query.connectionType == 'cooccurrence' ? '' : undefined,
      })),
      nodes: graphData.nodes.map((n) => ({
        ...n,
        color: getEntityColor(n.id.toString()),
      })),
    };
  }, [getEntityColor, graphData.edges, graphData.nodes, query.connectionType]);

  // Disable auto-stabilization on mount/setData — we trigger it manually above.
  const effectiveOptions = useMemo(
    () => ({
      ...options,
      physics: { ...options.physics, stabilization: { enabled: false } },
    }),
    [options],
  );

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
    <>
      <Box h="100vh" pos="relative">
        {selectedNode && <NodeInfo node={selectedNode} />}
        {selectedEdge && <EdgeInfo edge={selectedEdge} />}
        {isStabilizing && (
          <Stack
            gap={4}
            style={{
              position: 'absolute',
              top: 0,
              left: '25%',
              right: '25%',
              zIndex: 1000,
              padding: '6px 12px',
              background: 'rgba(0,0,0,0.75)',
            }}
          >
            <Text size="xs" c="white">
              Calculating layout...
            </Text>
            <Progress value={stabilizationProgress} animated size="sm" />
          </Stack>
        )}
        <Graph
          graph={coloredGraphData}
          events={events}
          options={effectiveOptions}
          getNetwork={handleGetNetwork}
        />
      </Box>
      <SideBar />
    </>
  );
};
