import React, { useEffect, useRef, useState } from 'react';
import { useServiceContext } from '../../contexts/ServiceContext';
import { useClickOutside } from '../../hooks/useClickOutside';
import { Identifiable } from '../../types/graph';
import { ClipLoader } from 'react-spinners';

interface EntityListEditorProps {
  ids: string[] | number[];
  onCloseOrClickOutside?: () => void;
  onRemove: (id: string | number) => void;
}

export const EntityListEditor: React.FC<EntityListEditorProps> = ({
  ids,
  onCloseOrClickOutside,
  onRemove,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => {
    if (onCloseOrClickOutside) onCloseOrClickOutside();
  });

  const [idsWithLabels, setIdsWithLabels] = useState<Identifiable[]>();
  const { entityService } = useServiceContext();
  useEffect(() => {
    if (ids) {
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
      {idsWithLabels &&
        idsWithLabels.map(({ id, label }) => (
          <div key={id} className={'panel__sub-panel'}>
            {label}
            &nbsp;
            <button style={{ background: 'red' }} onClick={() => onRemove(id)}>
              X
            </button>
          </div>
        ))}
    </div>
  );
};
