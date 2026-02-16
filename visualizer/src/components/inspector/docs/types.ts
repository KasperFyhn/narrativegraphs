import { Span } from '../../../types/doc';

export type HighlightContext =
  | { type: 'entity'; entityId: string | number }
  | {
      type: 'relation';
      subjectId: string | number;
      predicateId: string | number;
      objectId: string | number;
    }
  | {
      type: 'cooccurrence';
      entityOneId: string | number;
      entityTwoId: string | number;
    }
  | { type: 'entities'; entityIds: (string | number)[] };

export interface HighlightedSpan extends Span {
  role: 'subject' | 'predicate' | 'object';
  isPrimary: boolean; // true if this span is the main focus
  isEntityHighlight?: boolean; // true for focus entities in multi-entity mode
}

export interface SpanSegment {
  start: number;
  end: number;
  text: string;
  highlights: HighlightedSpan[];
}
