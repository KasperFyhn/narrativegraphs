import React, { PropsWithChildren, useRef } from 'react';
import { useClickOutside } from '../../hooks/useClickOutside';
import { Panel } from './Panel';
import './FloatingWindow.css';
import { X } from 'lucide-react';

interface FloatingWindowProps extends PropsWithChildren {
  title?: string;
  onCloseOrClickOutside?: () => void;
}

export const FloatingWindow: React.FC<FloatingWindowProps> = ({
  title,
  onCloseOrClickOutside,
  children,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => {
    if (onCloseOrClickOutside) onCloseOrClickOutside();
  });

  return (
    <Panel className={'floating-window flex-container--vertical'} ref={ref}>
      <div style={{ minHeight: '30px' }}>
        <button
          className={'floating-window__close-button'}
          onClick={onCloseOrClickOutside}
        >
          <X />
        </button>
        {title && <h2 style={{ margin: 0 }}>{title}</h2>}
      </div>
      {children}
    </Panel>
  );
};
