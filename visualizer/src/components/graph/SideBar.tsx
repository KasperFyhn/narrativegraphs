import React, { useRef } from 'react';
import { GraphOptionsPanel } from './controls/GraphOptionsPanel';
import {
  ArrowRight,
  Filter,
  Minus,
  LucideIcon,
  Puzzle,
  Search,
  Settings,
  ArrowBigRight,
} from 'lucide-react';
import { GraphFilterPanel } from './controls/GraphFilterPanel';
import { CommunitiesPanel } from './controls/CommunitiesPanel';
import { Panel } from '../common/Panel';
import './SideBar.css';
import { FocusPanel } from './controls/FocusPanel';
import { useClickOutside } from '../../hooks/useClickOutside';
import { useGraphQuery } from '../../hooks/useGraphQuery';

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
  const panelRefs = useRef<Record<ControlType, HTMLDivElement | null>>({
    search: null,
    filters: null,
    communities: null,
    settings: null,
  });

  const togglePanel = (panel: ControlType): void => {
    setActivePanel((prev) => (prev === panel ? null : panel));
  };

  const closePanel = (): void => setActivePanel(null);

  // Call the hook for whichever panel is active
  useClickOutside(
    { current: activePanel ? panelRefs.current[activePanel] : null },
    closePanel,
  );

  return (
    <div className="side-bar">
      {panels.map(({ type, icon: Icon, title, component: Component }) => (
        <div key={type} ref={(el) => (panelRefs.current[type] = el)}>
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
