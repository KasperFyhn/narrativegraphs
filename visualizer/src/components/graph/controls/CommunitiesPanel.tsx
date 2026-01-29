import React, { useEffect, useState } from 'react';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { Community } from '../../../types/graph';
import { EntityLabel } from '../../common/entity/EntityLabel';
import { ClipLoader } from 'react-spinners';
import {
  CommunitiesRequest,
  CommunityDetectionMethod,
  WeightMeasure,
} from '../../../types/graphQuery';
import { NamedInput } from '../../common/userinput/NamedInput';
import { RadioGroup } from '../../common/userinput/RadioGroup';

export const CommunitiesPanel: React.FC = () => {
  const { graphService } = useServiceContext();
  const { query, setConnectionType, filter, setFocusEntities } =
    useGraphQuery();

  const [communities, setCommunities] = useState<Community[] | null>([]);

  const [showIsolated, setShowIsolated] = useState(true);

  const [commRequest, setCommRequest] = useState<CommunitiesRequest>({
    weightMeasure: 'pmi',
    minWeight: 0.0,
    communityDetectionMethod: 'louvain',
    communityDetectionMethodArgs: {},
  });

  useEffect(() => {
    setCommunities([]);
  }, [commRequest]);

  return (
    <div>
      <div className={'flex-container flex-container--vertical'}>
        <NamedInput name={'Weight Measure'}>
          <RadioGroup
            name="weightMeasure"
            options={['pmi', 'frequency'] as const}
            value={commRequest.weightMeasure}
            onChange={(wm) =>
              setCommRequest({
                ...commRequest,
                weightMeasure: wm as WeightMeasure,
              })
            }
          />
        </NamedInput>
        <NamedInput name={'Min weight'}>
          <input
            type={'range'}
            min={-2}
            max={5}
            step={0.05}
            value={commRequest.minWeight}
            onChange={(e) =>
              setCommRequest({
                ...commRequest,
                minWeight: Number(e.target.value),
              })
            }
          />
          <div>{commRequest.minWeight.toPrecision(2)} </div>
        </NamedInput>
        <NamedInput name={'Algorithm'}>
          <RadioGroup
            name={'commDetectionMethod'}
            options={['louvain', 'k_clique', 'connected_components'] as const}
            value={commRequest.communityDetectionMethod}
            onChange={(choice) =>
              setCommRequest({
                ...commRequest,
                communityDetectionMethod: choice as CommunityDetectionMethod,
              })
            }
          />
        </NamedInput>
        <NamedInput name={'Show isolated'}>
          <input
            type={'checkbox'}
            checked={showIsolated}
            onChange={() => setShowIsolated(!showIsolated)}
          />
        </NamedInput>
      </div>
      <button
        style={{ marginTop: '10px', marginBottom: '3px' }}
        onClick={() => {
          if (query.connectionType !== 'cooccurrence') {
            setConnectionType('cooccurrence');
            alert(
              'Edges were set to cooccurrences.' +
                'To switch back, look under settings.',
            );
          }
          setCommunities(null);
          graphService
            .findCommunities(commRequest, filter)
            .then(setCommunities);
        }}
      >
        Find communities
      </button>
      <hr />
      <div>
        {communities === null && <ClipLoader loading={true} />}
        {communities !== null &&
          communities
            .filter((c) => c.conductance > 0 || showIsolated)
            .sort((c1, c2) =>
              commRequest.communityDetectionMethod === 'louvain'
                ? c2.members.length - c1.members.length
                : c2.score - c1.score,
            )
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
                    setFocusEntities(c.members.map((m) => m.id.toString()))
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
    </div>
  );
};
