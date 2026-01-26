import { useGraphQuery } from '../../../../hooks/useGraphQuery';
import React, { useEffect, useMemo } from 'react';
import { FloatingWindow } from '../../../common/FloatingWindow';

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
  const { filter, toggleCategoryValue, resetCategory } = useGraphQuery();

  const capitalizedName = useMemo(
    () => name.charAt(0).toUpperCase() + name.slice(1),
    [name],
  );

  const selected = useMemo((): string[] => {
    if (filter.categories === undefined) {
      return [];
    } else {
      return filter.categories[name] ?? [];
    }
  }, [filter.categories, name]);

  const [editing, setEditing] = React.useState<boolean>(false);

  const [selectedExpanded, setSelectedExpanded] = React.useState(false);
  useEffect(() => {
    if (selected.length < 4) setSelectedExpanded(false);
  }, [selected]);

  return (
    <div
      className={'flex-container--vertical panel__sub-panel'}
      style={{ width: '100%' }}
    >
      {showHeader && <>{capitalizedName}&nbsp;</>}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setEditing((prev) => !prev);
        }}
      >
        Edit
      </button>
      {editing && (
        <FloatingWindow
          title={'Categories'}
          onCloseOrClickOutside={() => setEditing(false)}
        >
          <div className={'flex-container'}>
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
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleCategoryValue(name, value);
                    }}
                  />
                  {value}
                </label>
              </div>
            ))}
          </div>
        </FloatingWindow>
      )}
      {selected.length === 0 && (
        <div>
          <i>All included</i>
        </div>
      )}
      {0 < selected.length && selected.length < 4 && (
        <div>{selected.join(', ')}</div>
      )}
      {4 <= selected.length && (
        <details>
          <summary onClick={() => setSelectedExpanded((prev) => !prev)}>
            {selectedExpanded ? '' : selected.slice(0, 3).join(', ') + ' ...'}
          </summary>
          {selected.join(', ')}
        </details>
      )}
    </div>
  );
};

export const CategorySelector: React.FC = () => {
  const { dataBounds } = useGraphQuery();

  return (
    <div className={'flex-container'} style={{ maxWidth: '175px' }}>
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
