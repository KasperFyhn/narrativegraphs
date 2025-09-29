export interface Identifiable {
  id: string | number;
  label: string;
}

export interface Node extends Identifiable {
  supernode?: Identifiable;
  subnodes?: Identifiable[];
  focus?: boolean;
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
