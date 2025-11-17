import React from 'react';
import { GraphOptionsPanel } from './controls/GraphOptionsPanel';
import { Filter, Puzzle, Settings } from 'lucide-react';
import { GraphFilterPanel } from './controls/GraphFilterPanel';
import { CommunitiesPanel } from './controls/CommunitiesPanel';
import { Panel } from '../common/Panel';
import './SideBar.css';

type ControlType = 'filters' | 'communities' | 'settings' | null;

interface ToggleButtonProps extends React.PropsWithChildren {
  onToggle: () => void;
  toggled: boolean;
}

const ToggleButton: React.FC<ToggleButtonProps> = ({
  onToggle,
  toggled,
  children,
}) => {
  return (
    <button
      onClick={onToggle}
      className={'toggle-button ' + (toggled ? 'toggle-button--toggled' : '')}
    >
      {children}
    </button>
  );
};

interface ControlPanelProps extends React.PropsWithChildren {
  hidden: boolean;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  hidden,
  children,
}: ControlPanelProps) => {
  return (
    <Panel
      className={'control-panel ' + (hidden ? '' : 'control-panel--hidden')}
    >
      {children}
    </Panel>
  );
};

export const SideBar: React.FC = () => {
  const [activePanel, setActivePanel] = React.useState<ControlType>(null);

  const togglePanel = (panel: ControlType): void => {
    setActivePanel((prev) => (prev === panel ? null : panel));
  };

  return (
    <div className="side-bar">
      <ToggleButton
        onToggle={() => togglePanel('filters')}
        toggled={activePanel === 'filters'}
      >
        <Filter />
      </ToggleButton>
      <ControlPanel hidden={activePanel === 'filters'}>
        <h2>Graph Filter Control</h2>
        <GraphFilterPanel />
      </ControlPanel>

      <ToggleButton
        onToggle={() => togglePanel('communities')}
        toggled={activePanel === 'communities'}
      >
        <Puzzle />
      </ToggleButton>
      <ControlPanel hidden={activePanel === 'communities'}>
        <h2>Sub-narrative Detection</h2>
        <CommunitiesPanel />
      </ControlPanel>

      <ToggleButton
        onToggle={() => togglePanel('settings')}
        toggled={activePanel === 'settings'}
      >
        <Settings />
      </ToggleButton>
      <ControlPanel hidden={activePanel === 'settings'}>
        <h2>Settings</h2>
        <GraphOptionsPanel />
      </ControlPanel>
    </div>
  );
};
