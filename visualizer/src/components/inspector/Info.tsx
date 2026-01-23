import React, { useCallback, useEffect, useState } from 'react';
import { Details } from '../../types/graph';
import { Doc } from '../../types/doc';
import { DocInfo } from './DocInfo';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../contexts/ServiceContext';
import './Info.css';
import { EntityService } from '../../services/EntityService';
import { RelationService } from '../../services/RelationService';
import { CooccurrenceService } from '../../services/CooccurrenceService';

export interface InfoProps {
  id: string | number;
  type: 'entity' | 'relation' | 'cooccurrence';
}

export const Info: React.FC<InfoProps> = ({ type, id }) => {
  const { entityService, relationService, cooccurrenceService } =
    useServiceContext();

  const [details, setDetails] = useState<Details>();
  const [docs, setDocs] = useState<Doc[] | null | undefined>(undefined);

  const getService = useCallback(():
    | EntityService
    | RelationService
    | CooccurrenceService => {
    switch (type) {
      case 'entity':
        return entityService;
      case 'relation':
        return relationService;
      case 'cooccurrence':
        return cooccurrenceService;
    }
  }, [cooccurrenceService, entityService, relationService, type]);

  useEffect(() => {
    setDetails(undefined);
    setDocs(undefined);

    getService().getDetails(id).then(setDetails);
  }, [getService, id]);

  const [visibleDocs, setVisibleDocs] = React.useState(50);

  const loadDocs = (): void => {
    setDocs(null);
    getService()
      .getDocs(id)
      .then((r) => {
        setDocs(r);
      });
  };

  const loadMore = (): void => {
    setVisibleDocs((prev) => prev + 50);
  };

  if (details === undefined) {
    return (
      <div>
        <ClipLoader loading={true} />
      </div>
    );
  }

  return (
    <>
      <p>Frequency: {details.stats.frequency}</p>
      <p>Document hits: {details.stats.docFrequency}</p>
      {details.stats.firstOccurrence && (
        <p>Earliest date: {details.stats.firstOccurrence.toString()}</p>
      )}
      {details.stats.lastOccurrence && (
        <p>Latest date: {details.stats.lastOccurrence.toString()}</p>
      )}
      {Object.entries(details.categories).map((entry) => {
        const [name, values] = entry;
        return (
          <p key={name}>
            {String(name).charAt(0).toUpperCase() + String(name).slice(1)}:{' '}
            {values.join(', ')}
          </p>
        );
      })}
      {details.altLabels && details.altLabels.length > 0 && (
        <div>
          Alternative Labels:
          <ul>
            {details.altLabels.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
      )}
      <div>
        {docs === undefined && <button onClick={loadDocs}>Load docs</button>}
        {docs === null && <ClipLoader loading={true} />}
        {docs && (
          <div>
            <button
              style={{ marginBottom: '3px' }}
              onClick={() => setDocs(undefined)}
            >
              Hide docs
            </button>
            {docs.slice(0, visibleDocs).map((d) => (
              <DocInfo
                key={d.id}
                document={d}
                subjectId={type === 'entity' ? details.id : undefined}
                predicateId={type === 'relation' ? details.id : undefined}
                objectId={type === 'entity' ? details.id : undefined}
              />
            ))}
            {visibleDocs < docs.length && (
              <button onClick={loadMore}>Load More</button>
            )}{' '}
          </div>
        )}
      </div>
    </>
  );
};
