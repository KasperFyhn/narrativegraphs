import React, { useEffect, useMemo, useState } from 'react';
import { RangeSlider, Text, Stack } from '@mantine/core';

interface LogarithmicRangeSliderProps {
  min: number;
  max: number;
  minValue: number;
  maxValue: number;
  onChange: (values: { minValue: number; maxValue: number }) => void;
  style?: React.CSSProperties;
  ruler?: boolean;
}

const linearToLog = (
  value: number,
  minLinear: number,
  maxLinear: number,
  minLog: number,
  maxLog: number,
): number => {
  const clampedValue = Math.max(minLinear, Math.min(value, maxLinear));
  const linearRange = maxLinear - minLinear;
  const logRange = Math.log(maxLog) - Math.log(minLog);
  const logValue =
    Math.log(minLog) + ((clampedValue - minLinear) / linearRange) * logRange;
  return Math.exp(logValue);
};

const logToLinear = (
  value: number,
  minLinear: number,
  maxLinear: number,
  minLog: number,
  maxLog: number,
): number => {
  const clampedValue = Math.max(minLog, Math.min(value, maxLog));
  const linearRange = maxLinear - minLinear;
  const logRange = Math.log(maxLog) - Math.log(minLog);
  const logValue = Math.log(clampedValue);
  return minLinear + ((logValue - Math.log(minLog)) / logRange) * linearRange;
};

const LogarithmicRangeSlider: React.FC<LogarithmicRangeSliderProps> = ({
  min,
  max,
  minValue,
  maxValue,
  onChange,
  style,
}) => {
  const linearMin = 0;
  const linearMax = 100;

  const [displayMin, setDisplayMin] = useState(Math.round(minValue));
  const [displayMax, setDisplayMax] = useState(Math.round(maxValue));

  useEffect(() => {
    setDisplayMin(minValue);
    setDisplayMax(maxValue);
  }, [minValue, maxValue]);

  const realValueToLinear = useMemo(
    () =>
      (realValue: number): number =>
        Math.round(logToLinear(realValue, linearMin, linearMax, min, max)),
    [min, max],
  );

  const linearToReal = useMemo(
    () =>
      (linearValue: number): number =>
        Math.round(linearToLog(linearValue, linearMin, linearMax, min, max)),
    [min, max],
  );

  return (
    <Stack gap={4} style={style}>
      <Text size="xs" c="dimmed">
        {displayMin} – {displayMax}
      </Text>
      <RangeSlider
        min={linearMin}
        max={linearMax}
        value={[realValueToLinear(minValue), realValueToLinear(maxValue)]}
        label={(v) => String(linearToReal(v))}
        onChange={([lo, hi]) => {
          setDisplayMin(linearToReal(lo));
          setDisplayMax(linearToReal(hi));
        }}
        onChangeEnd={([lo, hi]) => {
          const realMin = linearToReal(lo);
          const realMax = linearToReal(hi);
          onChange({ minValue: realMin, maxValue: realMax });
        }}
        size="sm"
        style={{ minWidth: 140 }}
      />
    </Stack>
  );
};

export default LogarithmicRangeSlider;
