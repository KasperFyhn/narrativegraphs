import React from 'react';
import { SpanSegment, HighlightedSpan } from './types';
import { segmentText } from './segmentText';
import './HighlightedText.css';

function getHighlightClasses(highlights: HighlightedSpan[]): string[] {
  const classes: string[] = ['highlight'];

  // Check if any highlight is primary
  const hasPrimary = highlights.some((h) => h.isPrimary);
  classes.push(hasPrimary ? 'highlight--primary' : 'highlight--secondary');

  // Add role-based classes (take first role if multiple overlapping)
  const roles = new Set(highlights.map((h) => h.role));
  if (roles.has('subject')) classes.push('highlight--subject');
  if (roles.has('predicate')) classes.push('highlight--predicate');
  if (roles.has('object')) classes.push('highlight--object');

  // Mark if multiple roles overlap (useful for styling edge cases)
  if (roles.size > 1) classes.push('highlight--multi-role');

  return classes;
}

interface SegmentSpanProps {
  segment: SpanSegment;
}

const SegmentSpan: React.FC<SegmentSpanProps> = ({ segment }) => {
  if (segment.highlights.length === 0) {
    return <span>{segment.text}</span>;
  }

  // Determine the CSS classes based on highlights
  const classes = getHighlightClasses(segment.highlights);

  return <span className={classes.join(' ')}>{segment.text}</span>;
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
