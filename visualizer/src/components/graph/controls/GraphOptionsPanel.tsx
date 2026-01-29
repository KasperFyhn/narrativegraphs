import React from 'react';
import '../graph.css';
import {
  isSmoothEnabled,
  useGraphOptionsContext,
} from '../../../contexts/GraphOptionsContext';
import { NamedInput } from '../../common/userinput/NamedInput';
import { ConnectionType, useGraphQuery } from '../../../hooks/useGraphQuery';
import { RadioGroup } from '../../common/userinput/RadioGroup';

export const GraphOptionsPanel: React.FC = () => {
  const { options, setOptions } = useGraphOptionsContext();
  const { query, setConnectionType } = useGraphQuery();
  return (
    <div className={'flex-container flex-container--vertical'}>
      <h3>Graph creation</h3>
      <NamedInput name={'Connection Type'}>
        <RadioGroup
          name={'connectionType'}
          options={['relation', 'cooccurrence']}
          value={query.connectionType}
          onChange={(choice) => setConnectionType(choice as ConnectionType)}
        />
      </NamedInput>

      <h3>Visuals</h3>
      <NamedInput name={'Physics'}>
        <input
          type={'checkbox'}
          checked={options.physics.enabled}
          onChange={(event) =>
            setOptions({
              ...options,
              physics: {
                ...options.physics,
                enabled: event.target.checked,
              },
            })
          }
        />
      </NamedInput>
      <NamedInput name={'Rounded Edges'}>
        <input
          type={'checkbox'}
          checked={isSmoothEnabled(options)}
          onChange={() =>
            setOptions({
              ...options,
              edges: {
                ...options.edges,
                smooth: !options.edges?.smooth,
              },
            })
          }
        />
      </NamedInput>
      <NamedInput name={'Edge Length'}>
        <input
          type="range"
          min="50"
          max="1000"
          value={options.physics.barnesHut.springLength}
          onChange={(event) =>
            setOptions({
              ...options,
              physics: {
                ...options.physics,
                barnesHut: {
                  springLength: Number(event.target.value),
                },
              },
            })
          }
        />
      </NamedInput>
    </div>
  );
};
