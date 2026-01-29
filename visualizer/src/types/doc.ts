export interface Span {
  id: string | number;
  start: number;
  end: number;
}

export interface Triplet {
  subject: Span;
  predicate: Span;
  object: Span;
}

export interface Tuplet {
  entityOne: Span;
  entityTwo: Span;
}

export interface Doc {
  id: string | number;
  strId: string;
  text: string;
  timestamp?: Date;
  triplets: Triplet[];
  tuplets: Tuplet[];
  categories: { [key: string]: string[] };
}
