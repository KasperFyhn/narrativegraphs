import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { StatsDisplay } from './StatsDisplay';
import { DocsSection } from '../docs/DocsSection';
import { Details } from '../../../types/graph';

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

  const loadDocs = useCallback(() => {
    return entityService.getDocs(id);
  }, [entityService, id]);

  const highlightContext = useMemo(
    () => ({ type: 'entity' as const, entityId: id }),
    [id],
  );

  if (loading) {
    return <ClipLoader loading={true} />;
  }

  if (!details) {
    return <p>Failed to load entity details.</p>;
  }

  const extra = [
    ...Object.entries(details.categories).map(([name, values]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: values.join(', '),
    })),
    ...(details.altLabels && details.altLabels.length > 0
      ? [
          {
            name: 'Alternative Labels',
            value:
              details.altLabels.slice(0, 10).join(', ') +
              (details.altLabels.length > 10 ? '...' : ''),
          },
        ]
      : []),
  ];

  return (
    <>
      <StatsDisplay stats={details.stats} extra={extra} />
      <DocsSection loadDocs={loadDocs} highlightContext={highlightContext} />
    </>
  );
};
