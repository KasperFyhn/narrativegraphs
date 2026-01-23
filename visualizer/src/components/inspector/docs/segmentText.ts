import { HighlightedSpan, SpanSegment } from './types';

/**
 * Segments text into non-overlapping chunks, each with its associated highlights.
 * Handles overlapping spans by creating segments at each span boundary.
 */
export function segmentText(
  text: string,
  highlights: HighlightedSpan[]
): SpanSegment[] {
  if (highlights.length === 0) {
    return [{ start: 0, end: text.length, text, highlights: [] }];
  }

  // Collect all unique boundary points
  const boundaries = new Set<number>([0, text.length]);
  for (const span of highlights) {
    boundaries.add(span.start);
    boundaries.add(span.end);
  }

  // Sort boundaries
  const sortedBoundaries = Array.from(boundaries).sort((a, b) => a - b);

  // Create segments between consecutive boundaries
  const segments: SpanSegment[] = [];
  for (let i = 0; i < sortedBoundaries.length - 1; i++) {
    const start = sortedBoundaries[i];
    const end = sortedBoundaries[i + 1];

    // Find all highlights that cover this segment
    const activeHighlights = highlights.filter(
      (h) => h.start <= start && h.end >= end
    );

    segments.push({
      start,
      end,
      text: text.slice(start, end),
      highlights: activeHighlights,
    });
  }

  return segments;
}
