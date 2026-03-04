import React, { PropsWithChildren } from 'react';
import { Modal } from '@mantine/core';

interface FloatingWindowProps extends PropsWithChildren {
  title?: string;
  onCloseOrClickOutside?: () => void;
}

export const FloatingWindow: React.FC<FloatingWindowProps> = ({
  title,
  onCloseOrClickOutside,
  children,
}) => (
  <Modal
    opened
    onClose={() => onCloseOrClickOutside?.()}
    title={title}
    centered
    size="lg"
  >
    {children}
  </Modal>
);
