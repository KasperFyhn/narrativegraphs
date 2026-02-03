import React from 'react';
import { Panel } from '../../common/Panel';
import { FocusEntitiesDocsSection } from '../docs/FocusEntitiesDocsSection';
import { useGraphQuery } from '../../../hooks/useGraphQuery';

export const FocusEntitiesContextsPane: React.FC = () => {
  const { query } = useGraphQuery();
  const entityCount = query.focusEntities?.length ?? 0;

  return (
    <Panel className="info-pane">
      <h2>Focus Entities Contexts</h2>
      <p>
        Showing text passages for {entityCount} focus{' '}
        {entityCount === 1 ? 'entity' : 'entities'}
      </p>
      <FocusEntitiesDocsSection />
    </Panel>
  );
};
