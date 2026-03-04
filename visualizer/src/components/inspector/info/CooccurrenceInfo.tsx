import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { StatsDisplay } from './StatsDisplay';
import { DocsSection } from '../docs/DocsSection';
import { CooccurrenceDetails } from '../../../types/graph';

interface CooccurrenceInfoProps {
  id: string | number;
}

export const CooccurrenceInfo: React.FC<CooccurrenceInfoProps> = ({ id }) => {
  const { cooccurrenceService } = useServiceContext();
  const [details, setDetails] = useState<CooccurrenceDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setDetails(null);

    cooccurrenceService
      .getDetails(id)
      .then((result) => setDetails(result as CooccurrenceDetails))
      .finally(() => setLoading(false));
  }, [cooccurrenceService, id]);

  const loadDocs = useCallback(() => {
    return cooccurrenceService.getDocs(id);
  }, [cooccurrenceService, id]);

  const highlightContext = useMemo(
    () =>
      details
        ? {
            type: 'cooccurrence' as const,
            entityOneId: details.entityOneId,
            entityTwoId: details.entityTwoId,
          }
        : undefined,
    [details],
  );

  if (!loading && !details) {
    return <p>Failed to load cooccurrence details.</p>;
  }

  return (
    <>
      {loading && <ClipLoader loading={true} />}
      {details && (
        <StatsDisplay
          stats={details.stats}
          extra={[
            { name: 'PMI', value: details.stats.pmi.toPrecision(3) },
            ...Object.entries(details.categories).map(([name, values]) => ({
              name: name.charAt(0).toUpperCase() + name.slice(1),
              value: values.join(', '),
            })),
          ]}
        />
      )}
      <DocsSection loadDocs={loadDocs} highlightContext={highlightContext} />
    </>
  );
};
