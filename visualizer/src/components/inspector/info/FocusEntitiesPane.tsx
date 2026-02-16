import React, { useCallback, useEffect, useState } from 'react';
import { Panel } from '../../common/Panel';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { DocsSection } from '../docs/DocsSection';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { HighlightContext } from '../docs/types';
import { Identifiable } from '../../../types/graph';
import { EntityLabel } from '../../common/entity/EntityLabel';

export const FocusEntitiesPane: React.FC = () => {
  const { query } = useGraphQuery();
  const entityCount = query.focusEntities?.length ?? 0;

  const { entityService } = useServiceContext();

  const [entityIds, setEntityIds] = useState<(string | number)[]>([]);
  const [entityLabels, setEntityLabels] = useState<Identifiable[]>([]);

  useEffect(() => {
    if (query.focusEntities) setEntityIds(query.focusEntities);
  }, [entityService, query.focusEntities]);

  useEffect(() => {
    if (entityIds.length > 0) {
      entityService.getLabels(entityIds).then(setEntityLabels);
    } else {
      setEntityLabels([]);
    }
  }, [entityIds, entityService]);

  const getDocs = useCallback(async () => {
    const docs = await entityService.getDocsByEntityIds(entityIds);
    const entityIdSet = new Set(entityIds.map(String));
    const docEntityCounts = new Map<string, number>();
    for (const doc of docs) {
      const matchedIds = new Set<string>();
      if (query.connectionType === 'relation') {
        for (const triplet of doc.triplets) {
          const subjectId = String(triplet.subject.id);
          const objectId = String(triplet.object.id);
          if (entityIdSet.has(subjectId)) matchedIds.add(subjectId);
          if (entityIdSet.has(objectId)) matchedIds.add(objectId);
        }
      } else {
        for (const tuplet of doc.tuplets) {
          const id1 = String(tuplet.entityOne.id);
          const id2 = String(tuplet.entityTwo.id);
          if (entityIdSet.has(id1)) matchedIds.add(id1);
          if (entityIdSet.has(id2)) matchedIds.add(id2);
        }
      }
      docEntityCounts.set(doc.strId, matchedIds.size);
    }
    docs.sort((a, b) => {
      const countA = docEntityCounts.get(a.strId) ?? 0;
      const countB = docEntityCounts.get(b.strId) ?? 0;
      return countB - countA;
    });
    return docs;
  }, [entityIds, entityService, query.connectionType]);

  const highlightContext: HighlightContext = {
    type: 'entities',
    entityIds,
  };

  return (
    <Panel className="info-pane">
      <h2>Focus Entities Contexts</h2>
      <p>
        Showing text passages for {entityCount} focus{' '}
        {entityCount === 1 ? 'entity' : 'entities'}
      </p>
      {entityIds.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginBottom: '12px',
          }}
        >
          {entityIds.map((id) => {
            const label =
              entityLabels.find((e) => String(e.id) === String(id))?.label ??
              String(id);
            return <EntityLabel key={id} id={id} label={label} />;
          })}
        </div>
      )}
      <DocsSection
        loadDocs={getDocs}
        highlightContext={highlightContext}
        autoload={true}
      />
    </Panel>
  );
};
