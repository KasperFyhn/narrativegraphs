export interface DataBounds {
  minimumPossibleNodeFrequency: number;
  maximumPossibleNodeFrequency: number;
  minimumPossibleEdgeFrequency: number;
  maximumPossibleEdgeFrequency: number;
  categories?: { [key: string]: string[] };
  earliestDate?: Date;
  latestDate?: Date;
}

export interface GraphQuery {
  connectionType: 'relation' | 'cooccurrence';
  focusEntities?: string[];
}

export interface GraphFilter {
  connectionType: 'relation' | 'cooccurrence';
  focusEntities?: string[];
  limitNodes: number;
  limitEdges: number;
  minimumNodeFrequency?: number;
  maximumNodeFrequency?: number;
  minimumEdgeFrequency?: number;
  maximumEdgeFrequency?: number;
  earliestDate?: Date;
  latestDate?: Date;
  blacklistedEntityIds?: string[];
  categories?: { [key: string]: string[] | undefined };
}

export const initialGraphQuery: GraphFilter = {
  connectionType: 'relation',
  limitNodes: 100,
  limitEdges: 200,
  // ... other defaults
};
