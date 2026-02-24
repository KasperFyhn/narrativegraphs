export interface DataBounds {
  minimumPossibleNodeFrequency: number;
  maximumPossibleNodeFrequency: number;
  minimumPossibleEdgeFrequency: number;
  maximumPossibleEdgeFrequency: number;
  categories?: { [key: string]: string[] };
  earliestDate?: Date;
  latestDate?: Date;
  earliestOrdinalTime?: number;
  latestOrdinalTime?: number;
}

export interface GraphQuery {
  connectionType: 'relation' | 'cooccurrence';
  focusEntities?: string[];
}

export interface GraphFilter {
  focusEntities?: string[];
  limitNodes: number;
  limitEdges: number;
  minimumNodeFrequency?: number;
  maximumNodeFrequency?: number;
  minimumEdgeFrequency?: number;
  maximumEdgeFrequency?: number;
  earliestDate?: Date;
  latestDate?: Date;
  earliestOrdinalTime?: number;
  latestOrdinalTime?: number;
  blacklistedEntityIds?: string[];
  categories?: { [key: string]: string[] | undefined };
}

export const initialGraphQuery: GraphFilter = {
  limitNodes: 100,
  limitEdges: 200,
  // ... other defaults
};

export type WeightMeasure = 'pmi' | 'frequency';
export type CommunityDetectionMethod =
  | 'louvain'
  | 'k_clique'
  | 'connected_components';

export interface CommunitiesRequest {
  weightMeasure: WeightMeasure;
  minWeight: number;
  communityDetectionMethod: CommunityDetectionMethod;
  communityDetectionMethodArgs: { [key: string]: string | number };
}
