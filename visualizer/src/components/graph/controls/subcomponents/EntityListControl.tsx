import React, { useEffect, useRef, useState } from 'react';
import { useServiceContext } from '../../../../contexts/ServiceContext';
import { useClickOutside } from '../../../../hooks/useClickOutside';
import { Identifiable } from '../../../../types/graph';
import { ClipLoader } from 'react-spinners';
import { useGraphQuery } from '../../../../hooks/useGraphQuery';
import { FloatingWindow } from '../../../common/FloatingWindow';

interface EntityListEditorProps {
  ids: string[] | number[];
  onCloseOrClickOutside?: () => void;
  onRemove: (id: string) => void;
  onClear?: () => void;
}

export const EntityListEditor: React.FC<EntityListEditorProps> = ({
  ids,
  onCloseOrClickOutside,
  onRemove,
  onClear,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => {
    if (onCloseOrClickOutside) onCloseOrClickOutside();
  });

  const [idsWithLabels, setIdsWithLabels] = useState<Identifiable[]>();
  const { entityService } = useServiceContext();
  useEffect(() => {
    if (ids && ids.length > 0) {
      entityService.getLabels(ids).then(setIdsWithLabels);
    } else {
      if (onCloseOrClickOutside) onCloseOrClickOutside();
    }
  }, [entityService, ids, onCloseOrClickOutside]);

  return (
    <FloatingWindow onCloseOrClickOutside={onCloseOrClickOutside}>
      <ClipLoader loading={idsWithLabels === undefined} />
      {onClear !== undefined && (
        <button style={{ background: 'red' }} onClick={onClear}>
          Clear all
        </button>
      )}
      <br />
      {idsWithLabels &&
        idsWithLabels.map(({ id, label }) => (
          <div key={id} className={'panel__sub-panel'}>
            {label}
            &nbsp;
            <button
              style={{ background: 'red' }}
              onClick={() => onRemove(String(id))}
            >
              X
            </button>
          </div>
        ))}
    </FloatingWindow>
  );
};

export const FocusEntitiesControl: React.FC = () => {
  const { query, removeFocusEntityId, clearFocusEntities } = useGraphQuery();

  const [editing, setEditing] = useState(false);

  return (
    <div className={'flex-container flex-container--vertical'}>
      <div>
        <span>
          <b>Double-click</b> to add or remove focus entities.
        </span>
      </div>
      <button
        disabled={
          query.focusEntities === undefined || query.focusEntities.length === 0
        }
        onClick={(e) => {
          e.stopPropagation();
          setEditing(true);
        }}
      >
        Edit focus entities
      </button>
      {query.focusEntities !== undefined && editing && (
        <EntityListEditor
          ids={query.focusEntities}
          onCloseOrClickOutside={() => setEditing(false)}
          onRemove={removeFocusEntityId}
          onClear={clearFocusEntities}
        />
      )}
    </div>
  );
};

export const EntityBlacklistControl: React.FC = () => {
  const { filter, removeBlacklistedEntityId, clearBlacklist } = useGraphQuery();

  const [editing, setEditing] = useState(false);

  return (
    <div className={'flex-container'}>
      <div>
        <b>Hold</b> or <b>shift+mark</b> to add nodes to blacklist.
      </div>
      <button
        disabled={
          filter.blacklistedEntityIds === undefined ||
          filter.blacklistedEntityIds.length === 0
        }
        onClick={(e) => {
          e.stopPropagation();
          setEditing((prev) => !prev);
        }}
      >
        Edit blacklist
      </button>
      {filter.blacklistedEntityIds !== undefined && editing && (
        <EntityListEditor
          ids={filter.blacklistedEntityIds}
          onCloseOrClickOutside={() => setEditing(false)}
          onRemove={removeBlacklistedEntityId}
          onClear={clearBlacklist}
        />
      )}
    </div>
  );
};
