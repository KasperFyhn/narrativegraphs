import { useGraphFilter } from '../../../hooks/useGraphFilter';
import React, { useMemo } from 'react';

interface CategorySelectorInnerProps {
  name: string;
  values: string[];
  showHeader?: boolean;
}

const CategorySelectorInner: React.FC<CategorySelectorInnerProps> = ({
  name,
  values,
  showHeader,
}) => {
  const { filter, toggleCategoryValue, resetCategory } = useGraphFilter();

  const selected = useMemo((): string[] => {
    if (filter.categories === undefined) {
      return [];
    } else {
      return filter.categories[name] ?? [];
    }
  }, [filter.categories, name]);

  const hasManyValues = useMemo(() => values.length > 5, [values]);

  const SelectBlock: React.FC = () => {
    return (
      <>
        <button
          onClick={() => resetCategory(name)}
          style={{ backgroundColor: 'red' }}
          disabled={selected.length === 0}
        >
          Reset
        </button>
        {values.sort().map((value) => (
          <div key={value} style={{ margin: '2px' }}>
            <label htmlFor={value}>
              <input
                type={'checkbox'}
                name={value}
                checked={selected.includes(value)}
                onChange={() => toggleCategoryValue(name, value)}
              />
              {value}
            </label>
          </div>
        ))}
      </>
    );
  };

  return (
    <div className={'flex-container--vertical'}>
      {hasManyValues ? (
        <details>
          <summary>{showHeader ? name : ' '}</summary>
          {<SelectBlock />}
        </details>
      ) : (
        <>
          {showHeader && <p>{name}</p>}
          <SelectBlock />
        </>
      )}
    </div>
  );
};

export const CategorySelector: React.FC = () => {
  const { dataBounds } = useGraphFilter();

  return (
    <div>
      {dataBounds.categories &&
        Object.entries(dataBounds.categories).map(([name, values]) => (
          <CategorySelectorInner
            key={name}
            name={name}
            values={values}
            showHeader={Object.keys(dataBounds.categories ?? []).length > 1}
          />
        ))}
    </div>
  );
};
