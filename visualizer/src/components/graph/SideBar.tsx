import React from 'react';
import { GraphOptionsPanel } from './controls/GraphOptionsPanel';
import { Filter, LucideIcon, Puzzle, Settings } from 'lucide-react';
import { GraphFilterPanel } from './controls/GraphFilterPanel';
import { HiddenControlPanel } from './controls/HiddenControlPanel';
import { CommunitiesPanel } from './controls/CommunitiesPanel';

export const SideBar: React.FC = () => {
  type PanelType = 'filters' | 'communities' | 'settings' | null;

  const [activePanel, setActivePanel] = React.useState<PanelType>(null);

  const togglePanel = (panel: PanelType): void => {
    setActivePanel((prev) => (prev === panel ? null : panel));
  };

  const ToggleButton = ({
    name,
    Icon,
  }: {
    name: PanelType;
    Icon: LucideIcon;
  }) => {
    return (
      <button
        onClick={() => togglePanel(name)}
        style={{
          backgroundColor: activePanel === name ? 'gray' : 'lightgray',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Icon size={22} />
      </button>
    );
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '50px', // Adjust width as needed
        height: '100vh',
        backgroundColor: 'rgba(245, 245, 245, .7)',
        padding: '5px',
        paddingTop: '10px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
      }}
    >
      <ToggleButton name={'filters'} Icon={Filter} />
      <HiddenControlPanel hidden={activePanel === 'filters'}>
        <h2>Graph Filter Control</h2>
        <GraphFilterPanel />
      </HiddenControlPanel>

      <ToggleButton name={'communities'} Icon={Puzzle} />
      <HiddenControlPanel hidden={activePanel === 'communities'}>
        <h2>Sub-narrative Detection</h2>
        <CommunitiesPanel />
      </HiddenControlPanel>

      <ToggleButton name={'settings'} Icon={Settings} />
      <HiddenControlPanel hidden={activePanel === 'settings'}>
        <h2>Settings</h2>
        <GraphOptionsPanel />
      </HiddenControlPanel>
    </div>
  );
};
