import React, { useCallback, useEffect, useState } from 'react';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { DocsSection } from './DocsSection';
import { HighlightContext } from './types';

interface FocusEntitiesDocsSectionProps {
  entityIds?: (string | number)[];
}

export const FocusEntitiesDocsSection: React.FC<
  FocusEntitiesDocsSectionProps
> = () => {
  const { entityService } = useServiceContext();
  const { query } = useGraphQuery();

  const [entityIds, setEntityIds] = useState<(string | number)[]>([]);

  useEffect(() => {
    if (query.focusEntities) setEntityIds(query.focusEntities);
  }, [entityService, query.focusEntities]);

  const getDocs = useCallback(() => {
    return entityService.getDocsByEntityIds(entityIds);
  }, [entityIds, entityService]);

  const highlightContext: HighlightContext = {
    type: 'entities',
    entityIds,
  };

  if (entityIds.length === 0) {
    return null;
  }

  return (
    <DocsSection
      loadDocs={getDocs}
      highlightContext={highlightContext}
      autoload={true}
    />
  );
};
