import React, { useEffect, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { StatsDisplay } from './StatsDisplay';
import { DocsSection } from '../docs/DocsSection';
import { Details } from '../../../types/graph';
import { CategoriesDisplay } from './CategoriesDisplay';
import { AltLabelsDisplay } from './AltLabelsDisplay';

interface EntityInfoProps {
  id: string | number;
}

export const EntityInfo: React.FC<EntityInfoProps> = ({ id }) => {
  const { entityService } = useServiceContext();
  const [details, setDetails] = useState<Details | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setDetails(null);

    entityService
      .getDetails(id)
      .then((result) => setDetails(result as Details))
      .finally(() => setLoading(false));
  }, [entityService, id]);

  if (loading) {
    return <ClipLoader loading={true} />;
  }

  if (!details) {
    return <p>Failed to load entity details.</p>;
  }

  return (
    <>
      <StatsDisplay stats={details.stats} />
      <CategoriesDisplay categories={details.categories} />
      <AltLabelsDisplay altLabels={details.altLabels} />
      <DocsSection
        loadDocs={() => entityService.getDocs(id)}
        highlightContext={{ type: 'entity', entityId: id }}
      />
    </>
  );
};
