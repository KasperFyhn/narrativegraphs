import React, { useEffect, useState } from 'react';
import { Stack, Group, Button, Text } from '@mantine/core';
import { useServiceContext } from '../../../../contexts/ServiceContext';
import { Identifiable } from '../../../../types/graph';
import { ClipLoader } from 'react-spinners';
import { useGraphQuery } from '../../../../hooks/useGraphQuery';
import { FloatingWindow } from '../../../common/FloatingWindow';
import { SubPanel } from '../../../common/Panel';

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
      <Stack gap="xs">
        <ClipLoader loading={idsWithLabels === undefined} />
        {onClear !== undefined && (
          <Button color="red" size="xs" onClick={onClear}>
            Clear all
          </Button>
        )}
        {idsWithLabels?.map(({ id, label }) => (
          <SubPanel key={id}>
            <Group justify="space-between" align="center">
              <Text size="sm">{label}</Text>
              <Button
                color="red"
                size="xs"
                onClick={() => onRemove(String(id))}
              >
                ✕
              </Button>
            </Group>
          </SubPanel>
        ))}
      </Stack>
    </FloatingWindow>
  );
};

export const FocusEntitiesControl: React.FC = () => {
  const { query, removeFocusEntityId, clearFocusEntities } = useGraphQuery();
  const [editing, setEditing] = useState(false);

  return (
    <Stack gap="xs">
      <Text size="sm">
        <b>Double-click</b> to add or remove focus entities.
      </Text>
      <Button
        size="xs"
        disabled={
          query.focusEntities === undefined || query.focusEntities.length === 0
        }
        onClick={(e) => {
          e.stopPropagation();
          setEditing(true);
        }}
      >
        Edit focus entities
      </Button>
      {query.focusEntities !== undefined && editing && (
        <EntityListEditor
          ids={query.focusEntities}
          onCloseOrClickOutside={() => setEditing(false)}
          onRemove={removeFocusEntityId}
          onClear={clearFocusEntities}
        />
      )}
    </Stack>
  );
};

export const EntityBlacklistControl: React.FC = () => {
  const { filter, removeBlacklistedEntityId, clearBlacklist } = useGraphQuery();
  const [editing, setEditing] = useState(false);

  return (
    <Group wrap="wrap">
      <Text size="sm">
        <b>Hold</b> or <b>shift+mark</b> to add nodes to blacklist.
      </Text>
      <Button
        size="xs"
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
      </Button>
      {filter.blacklistedEntityIds !== undefined && editing && (
        <EntityListEditor
          ids={filter.blacklistedEntityIds}
          onCloseOrClickOutside={() => setEditing(false)}
          onRemove={removeBlacklistedEntityId}
          onClear={clearBlacklist}
        />
      )}
    </Group>
  );
};
