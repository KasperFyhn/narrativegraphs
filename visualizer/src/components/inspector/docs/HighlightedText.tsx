import React from 'react';
import { SpanSegment, HighlightedSpan } from './types';
import { segmentText } from './segmentText';
import './HighlightedText.css';
import { useSelectionContext } from '../../../contexts/SelectionContext';

function getHighlightClasses(highlights: HighlightedSpan[]): string[] {
  const classes: string[] = ['highlight'];

  // Check if any highlight is primary
  const hasPrimary = highlights.some((h) => h.isPrimary);
  classes.push(hasPrimary ? 'highlight--primary' : 'highlight--secondary');

  // Add role-based classes for underline styling
  const roles = new Set(highlights.map((h) => h.role));
  if (roles.has('subject')) classes.push('highlight--subject');
  if (roles.has('predicate')) classes.push('highlight--predicate');
  if (roles.has('object')) classes.push('highlight--object');

  // Mark if multiple roles overlap
  if (roles.size > 1) classes.push('highlight--multi-role');

  return classes;
}

interface SegmentSpanProps {
  segment: SpanSegment;
}

const SegmentSpan: React.FC<SegmentSpanProps> = ({ segment }) => {
  const { getEntityColor } = useSelectionContext();

  if (segment.highlights.length === 0) {
    return <span>{segment.text}</span>;
  }

  // Determine the CSS classes based on highlights
  const classes = getHighlightClasses(segment.highlights);

  // Apply entity color as background - predicates get light green, others use getEntityColor
  const firstHighlight = segment.highlights[0];
  const opacity = firstHighlight.isPrimary ? 1.0 : 0.2;
  const style =
    firstHighlight.role === 'predicate'
      ? { backgroundColor: 'rgba(34, 197, 94, 0.2)' } // light green for predicates
      : { backgroundColor: getEntityColor(firstHighlight.id, opacity) };

  return (
    <span className={classes.join(' ')} style={style}>
      {segment.text}
    </span>
  );
};

interface HighlightedTextProps {
  text: string;
  highlights: HighlightedSpan[];
}

export const HighlightedText: React.FC<HighlightedTextProps> = ({
  text,
  highlights,
}) => {
  const segments = segmentText(text, highlights);

  return (
    <span className="highlighted-text">
      {segments.map((segment, index) => (
        <SegmentSpan key={`${segment.start}-${index}`} segment={segment} />
      ))}
    </span>
  );
};
