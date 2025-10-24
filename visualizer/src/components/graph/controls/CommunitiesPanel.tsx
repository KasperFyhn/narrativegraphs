import React, { useEffect, useState } from 'react';
import { useGraphFilter } from '../../../hooks/useGraphFilter';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { Community } from '../../../types/graph';
import { EntityLabel } from '../../common/entity/EntityLabel';
import { ClipLoader } from 'react-spinners';

export const CommunitiesPanel: React.FC = () => {
  const { graphService } = useServiceContext();
  const { filter, setWhitelistEntities } = useGraphFilter();

  const [communities, setCommunities] = useState<Community[] | null>([]);

  const [showIsolated, setShowIsolated] = useState(false);

  return (
    <div>
      <div>
        <button
          style={{ marginBottom: '3px' }}
          onClick={() => {
            setCommunities(null);
            graphService.findCommunities(filter).then(setCommunities);
          }}
        >
          Find communities
        </button>
        <br />
        Show isolated:{' '}
        <input
          type={'checkbox'}
          checked={showIsolated}
          onChange={() => setShowIsolated(!showIsolated)}
        />
      </div>

      {communities === null && <ClipLoader loading={true} />}
      {communities !== null &&
        communities
          .filter((c) => c.conductance > 0 || showIsolated)
          .sort((c1, c2) => c2.score - c1.score)
          .map((c, i) => (
            <div
              key={i}
              className={'panel__sub-panel'}
              style={{
                fontSize: 'small',
                position: 'relative',
              }}
            >
              <button
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  zIndex: 10,
                }}
                onClick={() =>
                  setWhitelistEntities(c.members.map((m) => m.id.toString()))
                }
              >
                Select
              </button>
              <p>Score: {c.score.toPrecision(3)}</p>
              <p>Density: {c.density.toPrecision(3)}</p>
              <p>Conductance: {c.conductance.toPrecision(3)}</p>
              <p>Avg. PMI: {c.avgPmi.toPrecision(3)}</p>
              <div className={'flex-container'}>
                {c.members.map((m) => (
                  <EntityLabel key={m.id} id={m.id} label={m.label} />
                ))}
              </div>
            </div>
          ))}
    </div>
  );
};
