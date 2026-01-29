export interface Identifiable {
  id: string | number;
  label: string;
}

export interface Node extends Identifiable {
  supernode?: Identifiable;
  subnodes?: Identifiable[];
}

export interface LabeledEdge extends Identifiable {
  subjectLabel: string;
  objectLabel: string;
}

export interface Edge extends Identifiable {
  from: number;
  to: number;
  subjectLabel: string;
  objectLabel: string;
  totalFrequency?: number;
  group: LabeledEdge[];
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

export interface Community {
  members: Identifiable[];
  score: number;
  density: number;
  avgPmi: number;
  conductance: number;
}

export interface TextStats {
  frequency: number;
  docFrequency: number;
  adjustedTfIdf: number;
  firstOccurrence?: Date | null;
  lastOccurrence?: Date | null;
}

export interface Details extends Identifiable {
  stats: TextStats;
  docs?: string[] | number[];
  altLabels?: string[];
  categories: { [key: string]: string[] };
}

export interface CooccurrenceStats extends TextStats {
  pmi: number;
}

export interface CooccurrenceDetails extends Details {
  entityOneId: number | string;
  entityTwoId: number | string;
  stats: CooccurrenceStats;
}

export interface RelationStats extends TextStats {
  significance: number;
}

export interface RelationDetails extends Details {
  subjectId: number | string;
  predicateId: number | string;
  objectId: number | string;
  stats: RelationStats;
}
