import React, { useEffect, useState } from 'react';
import { Button, Group, Modal } from '@mantine/core';
import { EntityLabel } from './EntityLabel';
import { Identifiable } from '../../../types/graph';
import { useServiceContext } from '../../../contexts/ServiceContext';

type EntityLabelListProps = (
  | { ids: (string | number)[]; entities?: never }
  | { entities: Identifiable[]; ids?: never }
) & {
  maxVisible?: number;
  modalTitle?: string;
  getAction?: (entity: Identifiable) => React.ReactNode;
};

export const EntityLabelList: React.FC<EntityLabelListProps> = ({
  ids,
  entities: entitiesProp,
  maxVisible = 8,
  modalTitle = 'Entities',
  getAction,
}) => {
  const { entityService } = useServiceContext();
  const [resolved, setResolved] = useState<Identifiable[]>(entitiesProp ?? []);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (entitiesProp) {
      setResolved(entitiesProp);
    } else if (ids && ids.length > 0) {
      entityService.getLabels(ids).then(setResolved);
    } else {
      setResolved([]);
    }
  }, [ids, entitiesProp, entityService]);

  const visible = resolved.slice(0, maxVisible);
  const overflow = resolved.length - maxVisible;

  return (
    <>
      <Group gap={4} wrap="wrap">
        {visible.map((entity) => (
          <EntityLabel
            key={entity.id}
            {...entity}
            rightSection={getAction?.(entity)}
          />
        ))}
        {overflow > 0 && (
          <Button size="xs" variant="subtle" onClick={() => setModalOpen(true)}>
            +{overflow} more
          </Button>
        )}
      </Group>

      <Modal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        title={modalTitle}
        size="md"
      >
        <Group gap={4} wrap="wrap">
          {resolved.map((entity) => (
            <EntityLabel
              key={entity.id}
              {...entity}
              rightSection={getAction?.(entity)}
            />
          ))}
        </Group>
      </Modal>
    </>
  );
};
