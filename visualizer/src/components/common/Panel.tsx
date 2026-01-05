import React, { ComponentPropsWithRef, PropsWithChildren } from 'react';
import './Panel.css';

interface PanelProps extends PropsWithChildren, ComponentPropsWithRef<'div'> {}

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
