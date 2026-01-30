import React, { useState, useEffect } from 'react';
import { ClipLoader } from 'react-spinners';
import { Doc } from '../../../types/doc';
import { DocInfo } from './DocInfo';
import { HighlightContext } from './types';

type LoadingState = 'idle' | 'loading' | 'loaded';

interface DocsSectionProps {
  loadDocs: () => Promise<Doc[]>;
  highlightContext?: HighlightContext;
  autoload?: boolean;
}

const PAGE_SIZE = 50;

export const DocsSection: React.FC<DocsSectionProps> = ({
  loadDocs,
  highlightContext,
  autoload = true,
}) => {
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [docs, setDocs] = useState<Doc[]>([]);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const handleLoad = async (): Promise<void> => {
    setLoadingState('loading');
    try {
      const result = await loadDocs();
      setDocs(result);
      setLoadingState('loaded');
    } catch (error) {
      console.error('Failed to load docs:', error);
      setLoadingState('idle');
    }
  };

  const handleHide = (): void => {
    setLoadingState('idle');
    setDocs([]);
    setVisibleCount(PAGE_SIZE);
  };

  const handleLoadMore = (): void => {
    setVisibleCount((prev) => prev + PAGE_SIZE);
  };

  useEffect(() => {
    if (autoload) handleLoad();
    // Should just run in the beginning
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loadingState === 'idle') {
    return <button onClick={handleLoad}>Load docs</button>;
  }

  if (loadingState === 'loading') {
    return <ClipLoader loading={true} />;
  }

  return (
    <div>
      <button style={{ marginBottom: '8px' }} onClick={handleHide}>
        Hide docs
      </button>
      {docs.slice(0, visibleCount).map((doc) => (
        <DocInfo
          key={doc.id}
          document={doc}
          highlightContext={highlightContext}
        />
      ))}
      {visibleCount < docs.length && (
        <button onClick={handleLoadMore}>
          Load More ({docs.length - visibleCount} remaining)
        </button>
      )}
    </div>
  );
};
