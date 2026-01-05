import React from 'react';
import './Panel.css';

type PanelProps = React.HTMLAttributes<HTMLDivElement>;

export const Panel: React.FC<PanelProps> = ({
  children,
  className,
  ...rest
}) => {
  return (
    <div className={'panel ' + (className || '')} {...rest}>
      {children}
    </div>
  );
};
