import React, { useEffect, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { StatsDisplay } from './StatsDisplay';
import { CategoriesDisplay } from './CategoriesDisplay';
import { AltLabelsDisplay } from './AltLabelsDisplay';
import { DocsSection } from '../docs/DocsSection';
import { RelationDetails } from '../../../types/graph';

interface RelationInfoProps {
  id: string | number;
  autoLoadDocs: boolean;
}

export const RelationInfo: React.FC<RelationInfoProps> = ({
  id,
  autoLoadDocs,
}) => {
  const { relationService } = useServiceContext();
  const [details, setDetails] = useState<RelationDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setDetails(null);

    relationService
      .getDetails(id)
      .then((result) => setDetails(result as RelationDetails))
      .finally(() => setLoading(false));
  }, [relationService, id]);

  if (loading) {
    return <ClipLoader loading={true} />;
  }

  if (!details) {
    return <p>Failed to load relation details.</p>;
  }

  return (
    <>
      <StatsDisplay
        stats={details.stats}
        extra={[
          {
            name: 'Significance',
            value: details.stats.significance.toPrecision(3),
          },
        ]}
      />
      <CategoriesDisplay categories={details.categories} />
      <AltLabelsDisplay altLabels={details.altLabels} />
      <DocsSection
        loadDocs={() => relationService.getDocs(id)}
        highlightContext={{
          type: 'relation',
          subjectId: details.subjectId,
          predicateId: details.predicateId,
          objectId: details.objectId,
        }}
        autoload={autoLoadDocs}
      />
    </>
  );
};
