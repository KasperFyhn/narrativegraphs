import React from 'react';

export interface HiddenControlPanelProps extends React.PropsWithChildren {
  hidden: boolean;
}

export const HiddenControlPanel: React.FC<HiddenControlPanelProps> = ({
  hidden,
  children,
}: HiddenControlPanelProps) => {
  return (
    <div
      className={
        'panel control-panel ' + (hidden ? '' : 'control-panel--hidden')
      }
    >
      {children}
    </div>
  );
};
