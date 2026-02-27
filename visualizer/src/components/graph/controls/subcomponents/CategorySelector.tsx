import { useGraphQuery } from '../../../../hooks/useGraphQuery';
import React, { useEffect, useMemo } from 'react';
import { Stack, Group, Button, Checkbox, Text } from '@mantine/core';
import { FloatingWindow } from '../../../common/FloatingWindow';
import { SubPanel } from '../../../common/Panel';

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
    if (filter.categories === undefined) return [];
    return filter.categories[name] ?? [];
  }, [filter.categories, name]);

  const [editing, setEditing] = React.useState<boolean>(false);
  const [selectedExpanded, setSelectedExpanded] = React.useState(false);

  useEffect(() => {
    if (selected.length < 4) setSelectedExpanded(false);
  }, [selected]);

  return (
    <SubPanel style={{ width: '100%' }}>
      <Stack gap="xs">
        {showHeader && (
          <Text size="sm" fw={500}>
            {capitalizedName}
          </Text>
        )}
        <Button
          size="xs"
          onClick={(e) => {
            e.stopPropagation();
            setEditing((prev) => !prev);
          }}
        >
          Edit
        </Button>
        {editing && (
          <FloatingWindow
            title="Categories"
            onCloseOrClickOutside={() => setEditing(false)}
          >
            <Stack gap="xs">
              <Button
                size="xs"
                color="red"
                onClick={() => resetCategory(name)}
                disabled={selected.length === 0}
              >
                Reset
              </Button>
              <Group gap="xs" wrap="wrap">
                {values.sort().map((value) => (
                  <Checkbox
                    key={value}
                    label={value}
                    checked={selected.includes(value)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleCategoryValue(name, value);
                    }}
                  />
                ))}
              </Group>
            </Stack>
          </FloatingWindow>
        )}
        {selected.length === 0 && (
          <Text size="xs" c="dimmed" fs="italic">
            All included
          </Text>
        )}
        {0 < selected.length && selected.length < 4 && (
          <Text size="xs">{selected.join(', ')}</Text>
        )}
        {4 <= selected.length && (
          <details>
            <summary onClick={() => setSelectedExpanded((prev) => !prev)}>
              {selectedExpanded ? '' : selected.slice(0, 3).join(', ') + ' ...'}
            </summary>
            <Text size="xs">{selected.join(', ')}</Text>
          </details>
        )}
      </Stack>
    </SubPanel>
  );
};

export const CategorySelector: React.FC = () => {
  const { dataBounds } = useGraphQuery();

  return (
    <Group gap="xs" style={{ maxWidth: '175px' }}>
      {dataBounds.categories &&
        Object.entries(dataBounds.categories).map(([name, values]) => (
          <CategorySelectorInner
            key={name}
            name={name}
            values={values}
            showHeader={Object.keys(dataBounds.categories ?? []).length > 1}
          />
        ))}
    </Group>
  );
};
