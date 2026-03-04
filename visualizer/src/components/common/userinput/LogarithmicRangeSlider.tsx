import React, { useEffect, useMemo, useState } from 'react';
import { RangeSlider, Text, Stack } from '@mantine/core';

interface LogarithmicRangeSliderProps {
  min: number;
  max: number;
  minValue: number;
  maxValue: number;
  onChange: (values: { minValue: number; maxValue: number }) => void;
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
}) => {
  const linearMin = 0;
  const linearMax = 100;

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

  // Internal state so thumbs track the mouse; parent is notified only on release
  const [sliderValue, setSliderValue] = useState<[number, number]>([
    realValueToLinear(minValue),
    realValueToLinear(maxValue),
  ]);

  useEffect(() => {
    setSliderValue([realValueToLinear(minValue), realValueToLinear(maxValue)]);
  }, [minValue, maxValue, realValueToLinear]);

  // Powers-of-10 tick marks to visualise the logarithmic scale
  const marks = useMemo(() => {
    const result: { value: number; label: string }[] = [];
    const minPow = Math.ceil(Math.log10(min));
    const maxPow = Math.floor(Math.log10(max));
    for (let p = minPow; p <= maxPow; p++) {
      const realVal = Math.pow(10, p);
      const label = realVal >= 1000 ? `${realVal / 1000}k` : String(realVal);
      result.push({ value: realValueToLinear(realVal), label });
    }
    return result;
  }, [min, max, realValueToLinear]);

  return (
    <RangeSlider
      min={linearMin}
      max={linearMax}
      value={sliderValue}
      label={(v) => String(linearToReal(v))}
      onChange={(value) => setSliderValue(value)}
      onChangeEnd={([lo, hi]) =>
        onChange({ minValue: linearToReal(lo), maxValue: linearToReal(hi) })
      }
      marks={marks}
      size="sm"
      style={{ minWidth: 140 }}
      mb={marks.length > 0 ? 'md' : 0}
    />
  );
};

export default LogarithmicRangeSlider;
