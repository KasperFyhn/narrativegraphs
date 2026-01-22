import React, { useEffect, useState } from 'react';
import { useGraphFilter } from '../../../hooks/useGraphFilter';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { Identifiable } from '../../../types/graph';
import { EntityLabel } from '../../common/entity/EntityLabel';
import { SubmittedTextInput } from '../../common/input/SubmittedTextInput';
import { SubPanel } from '../../common/Panel';
import { ClipLoader } from 'react-spinners';

export const SearchPanel: React.FC = () => {
  const { entityService } = useServiceContext();
  const { addWhitelistedEntityId } = useGraphFilter();

  const [labelSearch, setLabelSearch] = useState<string>('');
  const [results, setResults] = useState<Identifiable[] | null>([]);

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
      <SubmittedTextInput onSubmit={setLabelSearch} />
      <hr />
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
              <button
                onClick={() => addWhitelistedEntityId(result.id.toString())}
              >
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
