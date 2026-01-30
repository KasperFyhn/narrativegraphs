import React from 'react';
import { Edge } from '../../../types/graph';
import { Panel } from '../../common/Panel';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { RelationInfo } from './RelationInfo';
import { CooccurrenceInfo } from './CooccurrenceInfo';

interface RelationHeaderProps {
  subjectLabel: string;
  predicateLabel: string;
  objectLabel: string;
}

export const RelationHeader: React.FC<RelationHeaderProps> = ({
  subjectLabel,
  predicateLabel,
  objectLabel,
}) => {
  return (
    <h2>
      <i>{subjectLabel}</i> <b>{predicateLabel}</b> <i>{objectLabel}</i>
    </h2>
  );
};

interface CooccurrenceItemProps {
  id: string | number;
  subjectLabel: string;
  objectLabel: string;
}

const CooccurrenceItem: React.FC<CooccurrenceItemProps> = ({
  id,
  subjectLabel,
  objectLabel,
}) => {
  return (
    <div>
      <RelationHeader
        subjectLabel={subjectLabel}
        predicateLabel=" — "
        objectLabel={objectLabel}
      />
      <CooccurrenceInfo id={id} />
    </div>
  );
};

export interface EdgeInfoProps {
  edge: Edge;
  className?: string;
}

interface RelationGroupListProps {
  relations: Array<{
    id: string | number;
    label: string;
    subjectLabel: string;
    objectLabel: string;
  }>;
}

const RelationGroupList: React.FC<RelationGroupListProps> = ({ relations }) => {
  return (
    <>
      {relations.map((relation, index) => (
        <div key={relation.id}>
          <div>
            <RelationHeader
              subjectLabel={relation.subjectLabel}
              predicateLabel={relation.label}
              objectLabel={relation.objectLabel}
            />
            <RelationInfo
              id={relation.id}
              autoLoadDocs={relations.length === 1}
            />
          </div>
          {index + 1 < relations.length && (
            <>
              <br />
              <hr />
            </>
          )}
        </div>
      ))}
    </>
  );
};

export const EdgeInfo: React.FC<EdgeInfoProps> = ({ edge, className }) => {
  const { query } = useGraphQuery();

  return (
    <Panel className={`info-pane ${className ?? ''}`}>
      {query.connectionType === 'relation' && edge.group && (
        <RelationGroupList relations={edge.group} />
      )}
      {query.connectionType === 'cooccurrence' && (
        <CooccurrenceItem
          id={edge.id}
          subjectLabel={edge.subjectLabel}
          objectLabel={edge.objectLabel}
        />
      )}
    </Panel>
  );
};
