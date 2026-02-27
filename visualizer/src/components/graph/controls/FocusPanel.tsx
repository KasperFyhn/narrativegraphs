import React, { useEffect, useState } from 'react';
import { Stack, Group, Button, Text } from '@mantine/core';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { useSelectionContext } from '../../../contexts/SelectionContext';
import { Identifiable } from '../../../types/graph';
import { EntityLabel } from '../../common/entity/EntityLabel';
import { SubmittedTextInput } from '../../common/userinput/SubmittedTextInput';
import { SubPanel } from '../../common/Panel';
import { ClipLoader } from 'react-spinners';
import { FocusEntitiesControl } from './subcomponents/EntityListControl';
import { FocusEntitiesPane } from '../../inspector/info/FocusEntitiesPane';

export const FocusPanel: React.FC = () => {
  const { entityService } = useServiceContext();
  const { query, addFocusEntityId } = useGraphQuery();
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
      <FocusEntitiesControl />
      {showContextsPane && <FocusEntitiesPane />}
      <hr />
      <Text size="sm">Search:</Text>
      <SubmittedTextInput onSubmit={setLabelSearch} />

      {results == null && <ClipLoader loading={true} />}

      <Stack gap="xs">
        {results != null &&
          results.length > 0 &&
          results.map((result: Identifiable) => (
            <SubPanel key={result.id}>
              <Group justify="space-between" align="center">
                <EntityLabel {...result} />
                <Button
                  size="xs"
                  onClick={() => addFocusEntityId(result.id.toString())}
                >
                  +
                </Button>
              </Group>
            </SubPanel>
          ))}
      </Stack>

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
