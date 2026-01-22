import React from 'react';
import '../graph.css';
import {
  isSmoothEnabled,
  useGraphOptionsContext,
} from '../../../contexts/GraphOptionsContext';
import { NamedInput } from '../../common/input/NamedInput';

export const GraphOptionsPanel: React.FC = () => {
  const { options, setOptions } = useGraphOptionsContext();

  return (
    <div className={'flex-container flex-container--vertical'}>
      <NamedInput name={'Connection Type'}>
        <input type={'radio'} name={'Connection Type'} />
      </NamedInput>
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
