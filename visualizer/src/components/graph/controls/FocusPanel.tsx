import React, { useEffect, useState } from 'react';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { useSelectionContext } from '../../../contexts/SelectionContext';
import { Identifiable } from '../../../types/graph';
import { EntityLabel } from '../../common/entity/EntityLabel';
import { SubmittedTextInput } from '../../common/userinput/SubmittedTextInput';
import { SubPanel } from '../../common/Panel';
import { ClipLoader } from 'react-spinners';
import { FocusEntitiesControl } from './subcomponents/EntityListControl';
import { FocusEntitiesContextsPane } from '../../inspector/info/FocusEntitiesContextsPane';

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
    <div>
      <FocusEntitiesControl />
      {showContextsPane && <FocusEntitiesContextsPane />}
      <hr />
      <span>
        Search: <SubmittedTextInput onSubmit={setLabelSearch} />
      </span>
      <br />
      {results == null && <ClipLoader loading={results == null} />}
      {results != null &&
        results.length > 0 &&
        results.map((result: Identifiable) => {
          return (
            <SubPanel
              key={result.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <EntityLabel {...result} />
              <button onClick={() => addFocusEntityId(result.id.toString())}>
                +
              </button>
            </SubPanel>
          );
        })}
      {results != null && results.length === 0 && labelSearch !== '' && (
        <p>No results</p>
      )}
      {results != null && results.length === 0 && labelSearch === '' && (
        <p>Type your search string and hit Enter</p>
      )}
    </div>
  );
};
