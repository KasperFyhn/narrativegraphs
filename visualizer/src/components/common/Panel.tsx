import React, { PropsWithChildren, PropsWithRef } from 'react';
import './Panel.css';

interface PanelProps extends PropsWithChildren, PropsWithRef<any> {
  className?: string;
  style?: React.CSSProperties;
}

export const Panel: React.FC<PanelProps> = ({
  children,
  className,
  ...rest
}) => {
  return (
    <div className={'panel ' + className} {...rest}>
      {children}
    </div>
  );
};
