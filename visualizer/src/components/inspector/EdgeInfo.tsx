import React from 'react';
import { Info } from './Info';
import { Edge } from '../../types/graph';
import { Panel } from '../common/Panel';
import { ConnectionType, useGraphQuery } from '../../hooks/useGraphQuery';

interface RelationInfoProps {
  id: string | number;
  label: string;
  subjectLabel: string;
  objectLabel: string;
  connectionType: ConnectionType;
}

const RelationInfo: React.FC<RelationInfoProps> = ({
  id,
  label,
  subjectLabel,
  objectLabel,
  connectionType,
}) => {
  return (
    <div>
      <h2>
        <i>{subjectLabel}</i> <u>{label}</u> <i>{objectLabel}</i>
      </h2>
      <Info id={id} type={connectionType} />
    </div>
  );
};

export interface EdgeInfoProps {
  edge: Edge;
  className?: string;
}

export const EdgeInfo: React.FC<EdgeInfoProps> = ({
  edge,
  className,
}: EdgeInfoProps) => {
  const { query } = useGraphQuery();

  return (
    <Panel className={'node-info ' + className}>
      {query.connectionType === 'relation' &&
        edge.group &&
        edge.group.map((r, i) => (
          <div key={r.id}>
            <RelationInfo
              id={r.id}
              label={r.label}
              subjectLabel={r.subjectLabel}
              objectLabel={r.objectLabel}
              connectionType={query.connectionType}
            />
            {i + 1 < edge.group.length && (
              <>
                <br />
                <hr />
              </>
            )}
          </div>
        ))}
      {query.connectionType === 'cooccurrence' && (
        <RelationInfo
          id={edge.id}
          label={' -- '}
          subjectLabel={edge.subjectLabel}
          objectLabel={edge.objectLabel}
          connectionType={'cooccurrence'}
        />
      )}
    </Panel>
  );
};
