import React, { PropsWithChildren, useRef } from 'react';
import { useClickOutside } from '../../hooks/useClickOutside';

interface FloatingWindowProps extends PropsWithChildren {
  onCloseOrClickOutside?: () => void;
}

export const FloatingWindow: React.FC<FloatingWindowProps> = ({
  onCloseOrClickOutside,
  children,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => {
    if (onCloseOrClickOutside) onCloseOrClickOutside();
  });

  return (
    <div className={'panel list-editor flex-container'} ref={ref}>
      <button className={'panel__close-button'} onClick={onCloseOrClickOutside}>
        Close
      </button>
      {children}
    </div>
  );
};
