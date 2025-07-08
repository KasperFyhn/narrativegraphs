export interface DataBounds {
  minimumPossibleNodeFrequency: number;
  maximumPossibleNodeFrequency: number;
  minimumPossibleEdgeFrequency: number;
  maximumPossibleEdgeFrequency: number;
  categories?: string[];
  earliestDate?: Date;
  latestDate?: Date;
}

export interface GraphFilter {
  limitNodes: number;
  limitEdges: number;
  onlySupernodes?: boolean;
  minimumNodeFrequency?: number;
  maximumNodeFrequency?: number;
  minimumEdgeFrequency?: number;
  maximumEdgeFrequency?: number;
  labelSearch?: string;
  earliestDate?: Date;
  latestDate?: Date;
  whitelistedEntityIds?: string[];
  blacklistedEntityIds?: string[];
}

export type GraphFilterAction =
  | {
      type: 'SET_NODE_LIMITS';
      payload: { limitNodes: number; limitEdges: number };
    }
  | {
      type: 'SET_FREQUENCY_RANGE';
      payload: { min?: number; max?: number; target: 'node' | 'edge' };
    }
  | { type: 'SET_DATE_RANGE'; payload: { earliest?: Date; latest?: Date } }
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'TOGGLE_SUPERNODES' }
  | {
      type: 'UPDATE_ENTITY_LISTS';
      payload: { whitelist?: string[]; blacklist?: string[] };
    }
  | { type: 'RESET_FILTERS' }
  | { type: 'BULK_UPDATE'; payload: Partial<GraphFilter> };

export const initialGraphFilter: GraphFilter = {
  limitNodes: 100,
  limitEdges: 200,
  onlySupernodes: false,
  // ... other defaults
};
