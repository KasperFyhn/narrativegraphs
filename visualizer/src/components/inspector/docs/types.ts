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
    };

export interface HighlightedSpan extends Span {
  role: 'subject' | 'predicate' | 'object';
  isPrimary: boolean; // true if this span is the main focus
}

export interface SpanSegment {
  start: number;
  end: number;
  text: string;
  highlights: HighlightedSpan[];
}
