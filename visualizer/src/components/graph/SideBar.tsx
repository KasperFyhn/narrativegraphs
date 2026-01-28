import React from 'react';
import { GraphOptionsPanel } from './controls/GraphOptionsPanel';
import { Filter, LucideIcon, Puzzle, Search, Settings } from 'lucide-react';
import { GraphFilterPanel } from './controls/GraphFilterPanel';
import { CommunitiesPanel } from './controls/CommunitiesPanel';
import { Panel } from '../common/Panel';
import './SideBar.css';
import { FocusPanel } from './controls/FocusPanel';

type ControlType = 'search' | 'filters' | 'communities' | 'settings';

interface PanelConfig {
  type: ControlType;
  icon: LucideIcon;
  title: string;
  component: React.FC;
}

const panels: PanelConfig[] = [
  {
    type: 'search',
    icon: Search,
    title: 'Focus Entities',
    component: FocusPanel,
  },
  {
    type: 'filters',
    icon: Filter,
    title: 'Graph Filter Control',
    component: GraphFilterPanel,
  },
  {
    type: 'communities',
    icon: Puzzle,
    title: 'Sub-narrative Detection',
    component: CommunitiesPanel,
  },
  {
    type: 'settings',
    icon: Settings,
    title: 'Settings',
    component: GraphOptionsPanel,
  },
];

interface ToggleButtonProps extends React.PropsWithChildren {
  onToggle: () => void;
  toggled: boolean;
}

const ToggleButton: React.FC<ToggleButtonProps> = ({
  onToggle,
  toggled,
  children,
}) => (
  <button
    onClick={onToggle}
    className={'toggle-button ' + (toggled ? 'toggle-button--toggled' : '')}
  >
    {children}
  </button>
);

const ControlPanel: React.FC<React.PropsWithChildren> = ({ children }) => (
  <Panel className="control-panel">{children}</Panel>
);

export const SideBar: React.FC = () => {
  const [activePanel, setActivePanel] = React.useState<ControlType | null>(
    null,
  );

  const togglePanel = (panel: ControlType): void => {
    setActivePanel((prev) => (prev === panel ? null : panel));
  };

  return (
    <div className="side-bar">
      {panels.map(({ type, icon: Icon, title, component: Component }) => (
        <div key={type}>
          <ToggleButton
            onToggle={() => togglePanel(type)}
            toggled={activePanel === type}
          >
            <Icon />
          </ToggleButton>
          {activePanel === type && (
            <ControlPanel>
              <h2>{title}</h2>
              <Component />
            </ControlPanel>
          )}
        </div>
      ))}
    </div>
  );
};
