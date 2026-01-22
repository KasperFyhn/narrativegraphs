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

interface SubPanelProps
  extends PropsWithChildren,
    ComponentPropsWithRef<'div'> {}

export const SubPanel: React.FC<SubPanelProps> = ({
  children,
  className,
  ...rest
}) => {
  return (
    <div className={'panel__sub-panel ' + className} {...rest}>
      {children}
    </div>
  );
};
