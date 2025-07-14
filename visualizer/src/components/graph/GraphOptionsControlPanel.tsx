import React from 'react';
import './graph.css';
import {
  isSmoothEnabled,
  useGraphOptionsContext,
} from '../../contexts/GraphOptionsContext';

export const GraphOptionsControlPanel: React.FC = () => {
  const { options, setOptions } = useGraphOptionsContext();

  return (
    <div className={'flex-container flex-container--vertical'}>
      <div className={'flex-container'}>
        <span className={'option-span'}>Physics enabled:</span>
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
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Rounded edges:</span>
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
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Edge length:</span>
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
          step="1"
        />
      </div>
    </div>
  );
};
