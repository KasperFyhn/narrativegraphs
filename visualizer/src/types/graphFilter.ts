export interface DataBounds {
  minimumPossibleNodeFrequency: number;
  maximumPossibleNodeFrequency: number;
  minimumPossibleEdgeFrequency: number;
  maximumPossibleEdgeFrequency: number;
  categories?: { [key: string]: string[] };
  earliestDate?: Date;
  latestDate?: Date;
}

export interface GraphFilter {
  limitNodes: number;
  limitEdges: number;
  minimumNodeFrequency?: number;
  maximumNodeFrequency?: number;
  minimumEdgeFrequency?: number;
  maximumEdgeFrequency?: number;
  labelSearch?: string;
  earliestDate?: Date;
  latestDate?: Date;
  whitelistedEntityIds?: string[];
  blacklistedEntityIds?: string[];
  categories?: { [key: string]: string[] | undefined };
}

export const initialGraphFilter: GraphFilter = {
  limitNodes: 100,
  limitEdges: 200,
  // ... other defaults
};
