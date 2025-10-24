import React from 'react';

interface NamedInputProps extends React.PropsWithChildren {
  name: string;
  vertical?: boolean;
}

export const NamedInput: React.FC<NamedInputProps> = ({
  name,
  vertical,
  children,
}: NamedInputProps) => {
  return (
    <div
      className={
        'flex-container' + (vertical ? ' flex-container--vertical' : '')
      }
    >
      <span className={'option-span'} style={{ alignSelf: 'flex-start' }}>
        {name}
      </span>
      <div style={{ marginLeft: 'auto', padding: 0 }}>{children}</div>
    </div>
  );
};
