import React from 'react';
import '../graph.css';
import { Stack, Switch, Slider, Text } from '@mantine/core';
import {
  isSmoothEnabled,
  layoutPrecisionToParams,
  useGraphOptionsContext,
} from '../../../contexts/GraphOptionsContext';
import { ConnectionType, useGraphQuery } from '../../../hooks/useGraphQuery';
import { RadioGroup } from '../../common/userinput/RadioGroup';

export const GraphOptionsPanel: React.FC = () => {
  const { options, setOptions, layoutPrecision, setLayoutPrecision } =
    useGraphOptionsContext();
  const { query, setConnectionType, connectionTypes } = useGraphQuery();

  return (
    <Stack gap="md">
      <Text fw={600} size="sm">
        Graph creation
      </Text>
      <RadioGroup
        name="connectionType"
        label="Connection Type"
        options={connectionTypes}
        value={query.connectionType}
        onChange={(choice) => setConnectionType(choice as ConnectionType)}
      />

      <Text fw={600} size="sm">
        Visuals
      </Text>
      <Switch
        label="Physics"
        checked={options.physics.enabled}
        onChange={(e) =>
          setOptions({
            ...options,
            physics: { ...options.physics, enabled: e.currentTarget.checked },
          })
        }
      />
      <Switch
        label="Rounded Edges"
        checked={isSmoothEnabled(options)}
        onChange={() =>
          setOptions({
            ...options,
            edges: { ...options.edges, smooth: !options.edges?.smooth },
          })
        }
      />
      <Stack gap={4}>
        <Text size="sm">Edge Length</Text>
        <Slider
          min={50}
          max={1000}
          value={options.physics.barnesHut.springLength}
          label={(v) => String(v)}
          onChange={(v) =>
            setOptions({
              ...options,
              physics: {
                ...options.physics,
                barnesHut: { springLength: v },
              },
            })
          }
        />
      </Stack>
      <Stack gap={4}>
        <Text size="sm">Layout Precision </Text>
        <Slider
          min={0}
          max={100}
          value={layoutPrecision}
          label={(v) => {
            const { iterations, minVelocity } = layoutPrecisionToParams(v);
            return `${iterations} iter / v<${minVelocity.toFixed(1)}`;
          }}
          onChange={setLayoutPrecision}
        />
      </Stack>
    </Stack>
  );
};
