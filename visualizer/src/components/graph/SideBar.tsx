import React from 'react';
import { ActionIcon, Paper, Title } from '@mantine/core';
import { GraphOptionsPanel } from './controls/GraphOptionsPanel';
import { Filter, LucideIcon, Puzzle, Search, Settings } from 'lucide-react';
import { GraphFilterPanel } from './controls/GraphFilterPanel';
import { CommunitiesPanel } from './controls/CommunitiesPanel';
import './SideBar.css';
import { FocusPanel } from './controls/FocusPanel';

type ControlType = 'search' | 'filters' | 'communities' | 'settings';

interface PanelConfig {
  type: ControlType;
  icon: LucideIcon;
  title: string;
  component: React.FC;
  overflowY?: 'auto' | 'visible';
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
    overflowY: 'visible',
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
  <ActionIcon
    onClick={onToggle}
    variant={toggled ? 'filled' : 'default'}
    color="gray"
    size="lg"
  >
    {children}
  </ActionIcon>
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
      {panels.map(
        ({ type, icon: Icon, title, component: Component, overflowY }) => (
          <div key={type}>
            <ToggleButton
              onToggle={() => togglePanel(type)}
              toggled={activePanel === type}
            >
              <Icon />
            </ToggleButton>
            {activePanel === type && (
              <Paper
                withBorder
                radius="md"
                p="sm"
                className="control-panel"
                style={{ overflowY: overflowY ?? 'auto' }}
              >
                <Title order={1} size="h2" mb="sm">
                  {title}
                </Title>
                <Component />
              </Paper>
            )}
          </div>
        ),
      )}
    </div>
  );
};
