import React from 'react';
import { Stack, Group, Button, Switch, Slider, Text } from '@mantine/core';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { EntityLabel } from '../../common/entity/EntityLabel';
import { ClipLoader } from 'react-spinners';
import {
  CommunityDetectionMethod,
  WeightMeasure,
} from '../../../types/graphQuery';
import { RadioGroup } from '../../common/userinput/RadioGroup';
import { FocusEntitiesPane } from '../../inspector/info/FocusEntitiesPane';
import { useSelectionContext } from '../../../contexts/SelectionContext';
import { useCommunitiesContext } from '../../../contexts/CommunitiesContext';
import { SubPanel } from '../../common/Panel';

export const CommunitiesPanel: React.FC = () => {
  const { graphService } = useServiceContext();
  const { query, setConnectionType, filter, setFocusEntities } =
    useGraphQuery();
  const { hasSelection } = useSelectionContext();
  const {
    communities,
    setCommunities,
    commRequest,
    setCommRequest,
    showIsolated,
    setShowIsolated,
  } = useCommunitiesContext();

  const hasFocusEntities =
    query.focusEntities && query.focusEntities.length > 0;
  const showContextsPane = hasFocusEntities && !hasSelection;

  return (
    <Stack gap="md">
      {showContextsPane && <FocusEntitiesPane />}

      <RadioGroup
        name="weightMeasure"
        label="Weight Measure"
        options={['pmi', 'frequency'] as const}
        value={commRequest.weightMeasure}
        onChange={(wm) =>
          setCommRequest({ ...commRequest, weightMeasure: wm as WeightMeasure })
        }
      />

      <Stack gap={4}>
        <Text size="sm">
          Min weight: {commRequest.minWeight.toPrecision(2)}
        </Text>
        <Slider
          min={-2}
          max={5}
          step={0.05}
          value={commRequest.minWeight}
          label={(v) => v.toPrecision(2)}
          onChange={(v) => setCommRequest({ ...commRequest, minWeight: v })}
        />
      </Stack>

      <RadioGroup
        name="commDetectionMethod"
        label="Algorithm"
        options={['louvain', 'k_clique', 'connected_components'] as const}
        value={commRequest.communityDetectionMethod}
        onChange={(choice) =>
          setCommRequest({
            ...commRequest,
            communityDetectionMethod: choice as CommunityDetectionMethod,
          })
        }
      />

      <Switch
        label="Show isolated"
        checked={showIsolated}
        onChange={() => setShowIsolated(!showIsolated)}
      />

      <Button
        onClick={() => {
          if (query.connectionType !== 'cooccurrence') {
            setConnectionType('cooccurrence');
            alert(
              'Edges were set to cooccurrences. To switch back, look under settings.',
            );
          }
          setCommunities(null);
          graphService
            .findCommunities(commRequest, filter)
            .then(setCommunities);
        }}
      >
        Find communities
      </Button>

      <Stack gap="xs">
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
              <SubPanel
                key={i}
                style={{ fontSize: 'small', position: 'relative' }}
              >
                <Button
                  size="xs"
                  style={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    zIndex: 10,
                  }}
                  onClick={() =>
                    setFocusEntities(c.members.map((m) => m.id.toString()))
                  }
                >
                  Select
                </Button>
                <Text size="xs">Score: {c.score.toPrecision(3)}</Text>
                <Text size="xs">Density: {c.density.toPrecision(3)}</Text>
                <Text size="xs">
                  Conductance: {c.conductance.toPrecision(3)}
                </Text>
                <Text size="xs">Avg. PMI: {c.avgPmi.toPrecision(3)}</Text>
                <Group gap={4} wrap="wrap" mt={4}>
                  {c.members.map((m) => (
                    <EntityLabel key={m.id} id={m.id} label={m.label} />
                  ))}
                </Group>
              </SubPanel>
            ))}
      </Stack>
    </Stack>
  );
};
