import React from 'react';
import { GraphOptionsControlPanel } from './GraphOptionsControlPanel';
import {
  Filter,
  Settings,
  Calendar,
  ChevronRight,
  ChevronLeft,
  LucideIcon,
} from 'lucide-react';
import { GraphFilterControlPanel } from './FilterControlPanel/GraphFilterControlPanel';

export const SideBar: React.FC = () => {
  type PanelType = 'controls' | 'filters' | 'settings' | null;

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
    console.log(JSON.stringify(Icon));
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
        <Icon size={20} />
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
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
      }}
    >
      <ToggleButton name={'filters'} Icon={Filter} />
      <div
        className={
          'panel control-panel ' +
          (activePanel === 'filters' ? '' : 'control-panel--hidden')
        }
      >
        <GraphFilterControlPanel />
      </div>
      <ToggleButton name={'settings'} Icon={Settings} />
      <div
        className={
          'panel control-panel ' +
          (activePanel === 'settings' ? '' : 'control-panel--hidden')
        }
      >
        <GraphOptionsControlPanel />
      </div>
    </div>
  );
};
