import React from 'react';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { HighlightContext } from './types';
import { extractHighlights } from './extractHighlights';
import { HighlightedText } from './HighlightedText';
import './DocInfo.css';
import { Doc } from '../../../types/doc';

interface DocInfoProps {
  document: Doc;
  highlightContext?: HighlightContext;
}

export const DocInfo: React.FC<DocInfoProps> = ({
  document,
  highlightContext,
}) => {
  const { query } = useGraphQuery();

  const highlights = highlightContext
    ? extractHighlights(document, highlightContext, query.connectionType)
    : [];

  return (
    <div className="doc-info">
      <div className="doc-info__header">
        <span className="doc-info__id">{document.id}</span>
        {document.timestamp && (
          <span className="doc-info__date">
            {document.timestamp.toString()}
          </span>
        )}
      </div>

      {document.strId && <p className="doc-info__id">{document.strId}</p>}

      {Object.entries(document.categories).length > 0 && (
        <div className="doc-info__categories">
          {Object.entries(document.categories).map(([name, values]) => (
            <span key={name} className="doc-info__category">
              {name}: {values.join(', ')}
            </span>
          ))}
        </div>
      )}

      <div className="doc-info__text">
        {highlights.length > 0 ? (
          <HighlightedText text={document.text} highlights={highlights} />
        ) : (
          <span>{document.text}</span>
        )}
      </div>
    </div>
  );
};
