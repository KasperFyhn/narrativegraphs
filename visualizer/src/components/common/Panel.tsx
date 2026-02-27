import React, { PropsWithChildren } from 'react';
import { Paper, PaperProps } from '@mantine/core';

interface PanelProps extends PropsWithChildren, Omit<PaperProps, 'children'> {
  className?: string;
}

export const Panel: React.FC<PanelProps> = ({
  children,
  className,
  style,
  ...rest
}) => (
  <Paper
    withBorder
    radius="md"
    p="sm"
    className={className}
    style={{ overflowY: 'auto', ...style }}
    {...rest}
  >
    {children}
  </Paper>
);

interface SubPanelProps
  extends PropsWithChildren,
    Omit<PaperProps, 'children'> {
  className?: string;
}

export const SubPanel: React.FC<SubPanelProps> = ({
  children,
  className,
  style,
  ...rest
}) => (
  <Paper
    withBorder
    radius="sm"
    p="xs"
    mb={4}
    className={className}
    style={style}
    {...rest}
  >
    {children}
  </Paper>
);
