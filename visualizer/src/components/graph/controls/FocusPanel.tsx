import React, { useEffect, useState } from 'react';
import { Stack, Text, ActionIcon, Group, Button } from '@mantine/core';
import { Minus, Plus } from 'lucide-react';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { Identifiable } from '../../../types/graph';
import { SubmittedTextInput } from '../../common/userinput/SubmittedTextInput';
import { ClipLoader } from 'react-spinners';
import { FocusEntitiesInfo } from '../../inspector/info/FocusEntitiesInfo';
import { EntityLabelList } from '../../common/entity/EntityLabelList';
import { useSelectionContext } from '../../../contexts/SelectionContext';

export const FocusPanel: React.FC = () => {
  const { entityService } = useServiceContext();
  const { query, addFocusEntityId, removeFocusEntityId, clearFocusEntities } =
    useGraphQuery();
  const { hasSelection } = useSelectionContext();
  const [labelSearch, setLabelSearch] = useState<string>('');
  const [results, setResults] = useState<Identifiable[] | null>([]);

  const hasFocusEntities =
    query.focusEntities && query.focusEntities.length > 0;
  const showContextsPane = hasFocusEntities && !hasSelection;

  useEffect(() => {
    if (labelSearch && labelSearch.length > 0) {
      setResults(null);
      entityService.search(labelSearch).then(setResults);
    } else {
      setResults([]);
    }
  }, [entityService, labelSearch]);

  return (
    <Stack gap="sm">
      <Text size="sm">
        <b>Double-click</b> a node in the graph to add or remove focus entities.
      </Text>
      {showContextsPane && <FocusEntitiesInfo />}
      <hr />

      {query.focusEntities && query.focusEntities.length > 0 && (
        <>
          <EntityLabelList
            ids={query.focusEntities}
            maxVisible={10}
            modalTitle="Focus entities"
            getAction={(entity) => (
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ActionIcon
                  size="xs"
                  variant="filled"
                  color="red"
                  style={{ border: '1px solid rgba(255,255,255,0.5)' }}
                  onClick={() => removeFocusEntityId(String(entity.id))}
                >
                  <Minus size={10} />
                </ActionIcon>
              </div>
            )}
          />
          <Group gap="xs" mt="xs" mb="sm">
            <Button
              size="xs"
              variant="subtle"
              color="red"
              onClick={clearFocusEntities}
            >
              Clear all
            </Button>
          </Group>
        </>
      )}

      <Text size="sm">Search:</Text>
      <SubmittedTextInput onSubmit={setLabelSearch} />

      {results == null && <ClipLoader loading={true} />}

      {results != null && results.length > 0 && (
        <EntityLabelList
          entities={results}
          maxVisible={Infinity}
          getAction={(entity) => {
            const isFocused = query.focusEntities?.includes(
              entity.id.toString(),
            );
            return (
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ActionIcon
                  size="xs"
                  variant="filled"
                  color={isFocused ? 'red' : 'green'}
                  style={{ border: '1px solid rgba(255,255,255,0.5)' }}
                  onClick={() =>
                    isFocused
                      ? removeFocusEntityId(entity.id.toString())
                      : addFocusEntityId(entity.id.toString())
                  }
                >
                  {isFocused ? <Minus size={10} /> : <Plus size={10} />}
                </ActionIcon>
              </div>
            );
          }}
        />
      )}

      {results != null && results.length === 0 && labelSearch !== '' && (
        <Text size="sm" c="dimmed">
          No results
        </Text>
      )}
      {results != null && results.length === 0 && labelSearch === '' && (
        <Text size="sm" c="dimmed">
          Type your search string and hit Enter
        </Text>
      )}
    </Stack>
  );
};
