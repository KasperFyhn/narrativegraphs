import React, { useEffect, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { StatsDisplay } from './StatsDisplay';
import { DocsSection } from '../docs/DocsSection';
import { CooccurrenceDetails } from '../../../types/graph';
import { CategoriesDisplay } from './CategoriesDisplay';

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

  if (loading) {
    return <ClipLoader loading={true} />;
  }

  if (!details) {
    return <p>Failed to load cooccurrence details.</p>;
  }

  return (
    <>
      <StatsDisplay
        stats={details.stats}
        extra={[{ name: 'PMI', value: details.stats.pmi.toPrecision(3) }]}
      />
      <CategoriesDisplay categories={details.categories} />
      <DocsSection
        loadDocs={() => cooccurrenceService.getDocs(id)}
        highlightContext={{
          type: 'cooccurrence',
          entityOneId: details.entityOneId,
          entityTwoId: details.entityTwoId,
        }}
      />
    </>
  );
};
