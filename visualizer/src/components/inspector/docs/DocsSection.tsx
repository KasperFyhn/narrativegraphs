import React, { useState, useEffect } from 'react';
import { Button, Stack } from '@mantine/core';
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loadingState === 'idle') {
    return (
      <Button size="xs" variant="subtle" onClick={handleLoad}>
        Load docs
      </Button>
    );
  }

  if (loadingState === 'loading') {
    return <ClipLoader loading={true} />;
  }

  return (
    <Stack gap="xs" align="flex-start">
      <Button size="xs" variant="subtle" onClick={handleHide}>
        Hide docs
      </Button>
      {docs.slice(0, visibleCount).map((doc) => (
        <DocInfo
          key={doc.id}
          document={doc}
          highlightContext={highlightContext}
        />
      ))}
      {visibleCount < docs.length && (
        <Button size="xs" variant="subtle" onClick={handleLoadMore}>
          Load More ({docs.length - visibleCount} remaining)
        </Button>
      )}
    </Stack>
  );
};
