import React, { useEffect, useRef, useState } from 'react';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { useClickOutside } from '../../../hooks/useClickOutside';
import { Identifiable } from '../../../types/graph';
import { ClipLoader } from 'react-spinners';
import { useGraphFilter } from '../../../hooks/useGraphFilter';

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
    <div className={'panel list-editor flex-container'} ref={ref}>
      <button className={'panel__close-button'} onClick={onCloseOrClickOutside}>
        Close
      </button>
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
    </div>
  );
};

export const EntityWhitelistControl: React.FC = () => {
  const { filter, removeWhitelistedEntityId, clearWhitelist } =
    useGraphFilter();

  const [editing, setEditing] = useState(false);

  return (
    <div className={'flex-container flex-container--vertical'}>
      <div>
        <span>
          <b>Double-click</b> to add or remove nodes from whitelist.
        </span>
      </div>
      <button
        disabled={
          filter.whitelistedEntityIds === undefined ||
          filter.whitelistedEntityIds.length === 0
        }
        onClick={(e) => {
          e.stopPropagation();
          setEditing(true);
        }}
      >
        Edit whitelist
      </button>
      {filter.whitelistedEntityIds !== undefined && editing && (
        <EntityListEditor
          ids={filter.whitelistedEntityIds}
          onCloseOrClickOutside={() => setEditing(false)}
          onRemove={removeWhitelistedEntityId}
          onClear={clearWhitelist}
        />
      )}
    </div>
  );
};

export const EntityBlacklistControl: React.FC = () => {
  const { filter, removeBlacklistedEntityId, clearBlacklist } =
    useGraphFilter();

  const [editing, setEditing] = useState(false);

  return (
    <div className={'flex-container'}>
      <div>
        <b>Hold</b> or <b>shift+mark</b> to add nodes to blacklist.
      </div>
      {/*<button*/}
      {/*  disabled={isBlacklistEmpty}*/}
      {/*  onClick={}*/}
      {/*>*/}
      {/*  &#8617;*/}
      {/*</button>*/}
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
