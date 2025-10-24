import React, { PropsWithChildren } from 'react';

export const Panel: React.FC<PropsWithChildren> = ({ children }) => {
  return <div className="panel">{children}</div>;
};
