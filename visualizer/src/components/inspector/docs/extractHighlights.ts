import { Doc, Span } from '../../../types/doc';
import { HighlightContext, HighlightedSpan } from './types';
import { ConnectionType } from '../../../hooks/useGraphQuery';

function toHighlightedSpan(
  span: Span,
  role: 'subject' | 'predicate' | 'object',
  isPrimary: boolean,
): HighlightedSpan {
  return {
    ...span,
    role,
    isPrimary,
  };
}

/**
 * For entity context: highlight all occurrences of the entity as primary,
 * and related spans (from triplets/tuplets containing this entity) as secondary.
 */
function extractEntityHighlights(
  doc: Doc,
  entityId: string | number,
  connectionType: ConnectionType,
): HighlightedSpan[] {
  const highlights: HighlightedSpan[] = [];

  if (connectionType === 'relation') {
    for (const triplet of doc.triplets) {
      const entityIsSubject = triplet.subject.id === entityId;
      const entityIsObject = triplet.object.id === entityId;

      if (entityIsSubject || entityIsObject) {
        // The entity span is primary, others are secondary context
        highlights.push(
          toHighlightedSpan(triplet.subject, 'subject', entityIsSubject),
        );
        highlights.push(
          toHighlightedSpan(triplet.predicate, 'predicate', false),
        );
        highlights.push(
          toHighlightedSpan(triplet.object, 'object', entityIsObject),
        );
      }
    }
  } else {
    // cooccurrence mode
    for (const tuplet of doc.tuplets) {
      const entityIsSubject = tuplet.entityOne.id === entityId;
      const entityIsObject = tuplet.entityTwo.id === entityId;

      if (entityIsSubject || entityIsObject) {
        highlights.push(
          toHighlightedSpan(
            tuplet.entityOne,
            entityIsSubject ? 'subject' : 'object',
            entityIsSubject,
          ),
        );
        highlights.push(
          toHighlightedSpan(
            tuplet.entityTwo,
            entityIsObject ? 'subject' : 'object',
            entityIsObject,
          ),
        );
      }
    }
  }

  return highlights;
}

/**
 * For relation context: highlight triplets where all three IDs match.
 */
function extractRelationHighlights(
  doc: Doc,
  subjectId: string | number,
  predicateId: string | number,
  objectId: string | number,
): HighlightedSpan[] {
  const highlights: HighlightedSpan[] = [];

  for (const triplet of doc.triplets) {
    const matches =
      triplet.subject.id === subjectId &&
      triplet.predicate.id === predicateId &&
      triplet.object.id === objectId;

    if (matches) {
      highlights.push(toHighlightedSpan(triplet.subject, 'subject', true));
      highlights.push(toHighlightedSpan(triplet.predicate, 'predicate', true));
      highlights.push(toHighlightedSpan(triplet.object, 'object', true));
    }
  }

  return highlights;
}

/**
 * For cooccurrence context: highlight tuplets where both IDs match.
 */
function extractCooccurrenceHighlights(
  doc: Doc,
  subjectId: string | number,
  objectId: string | number,
): HighlightedSpan[] {
  const highlights: HighlightedSpan[] = [];

  for (const tuplet of doc.tuplets) {
    // Check both orderings since cooccurrence is symmetric
    const matchesForward =
      tuplet.entityOne.id === subjectId && tuplet.entityTwo.id === objectId;
    const matchesReverse =
      tuplet.entityOne.id === objectId && tuplet.entityTwo.id === subjectId;

    if (matchesForward) {
      highlights.push(toHighlightedSpan(tuplet.entityOne, 'subject', true));
      highlights.push(toHighlightedSpan(tuplet.entityTwo, 'object', true));
    } else if (matchesReverse) {
      highlights.push(toHighlightedSpan(tuplet.entityTwo, 'subject', true));
      highlights.push(toHighlightedSpan(tuplet.entityOne, 'object', true));
    }
  }

  return highlights;
}

/**
 * Extracts highlighted spans from a document based on the highlight context.
 */
export function extractHighlights(
  doc: Doc,
  context: HighlightContext,
  connectionType: ConnectionType,
): HighlightedSpan[] {
  console.log(context);
  console.log(doc.triplets);
  switch (context.type) {
    case 'entity':
      return extractEntityHighlights(doc, context.entityId, connectionType);
    case 'relation':
      return extractRelationHighlights(
        doc,
        context.subjectId,
        context.predicateId,
        context.objectId,
      );
    case 'cooccurrence':
      return extractCooccurrenceHighlights(
        doc,
        context.entityOneId,
        context.entityTwoId,
      );
  }
}
