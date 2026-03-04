import React from 'react';
import {
  Alert,
  Button,
  Group,
  Slider,
  Stack,
  Switch,
  Table,
  Text,
} from '@mantine/core';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { useServiceContext } from '../../../contexts/ServiceContext';
import { EntityLabelList } from '../../common/entity/EntityLabelList';
import { ClipLoader } from 'react-spinners';
import {
  CommunityDetectionMethod,
  WeightMeasure,
} from '../../../types/graphQuery';
import { RadioGroup } from '../../common/userinput/RadioGroup';
import { FocusEntitiesInfo } from '../../inspector/info/FocusEntitiesInfo';
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
      {showContextsPane && <FocusEntitiesInfo />}

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
        options={['louvain', 'k_clique'] as const}
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

      {query.connectionType !== 'cooccurrence' && (
        <Alert variant="light" color="blue">
          Running community detection will switch edges to co-occurrences.
        </Alert>
      )}

      <Button
        onClick={() => {
          if (query.connectionType !== 'cooccurrence') {
            setConnectionType('cooccurrence');
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
              <SubPanel key={i}>
                <Table withRowBorders={false} fz="sm">
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td fw={500}>Score</Table.Td>
                      <Table.Td>{c.score.toPrecision(3)}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={500}>Density</Table.Td>
                      <Table.Td>{c.density.toPrecision(3)}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={500}>Conductance</Table.Td>
                      <Table.Td>{c.conductance.toPrecision(3)}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={500}>Avg. PMI</Table.Td>
                      <Table.Td>{c.avgPmi.toPrecision(3)}</Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
                <EntityLabelList
                  entities={c.members}
                  maxVisible={8}
                  modalTitle="Community members"
                />
                <Button
                  size="xs"
                  mt={10}
                  onClick={() =>
                    setFocusEntities(c.members.map((m) => m.id.toString()))
                  }
                >
                  Select
                </Button>
              </SubPanel>
            ))}
      </Stack>
    </Stack>
  );
};
