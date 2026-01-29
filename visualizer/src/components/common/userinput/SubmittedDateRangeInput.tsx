import React from 'react';

export interface SubmittedDataRangeInputProps {
  min: Date;
  initStartDate?: Date;
  initEndDate?: Date;
  max: Date;
  onSubmit: (start: Date, end: Date) => void;
}

function str(date?: Date): string | undefined {
  if (!date) {
    return undefined;
  }
  return date.toLocaleDateString('en-CA');
}

export const SubmittedDataRangeInput: React.FC<
  SubmittedDataRangeInputProps
> = ({
  min,
  initStartDate,
  initEndDate,
  max,
  onSubmit,
}: SubmittedDataRangeInputProps) => {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const startDateStr = formData.get('startDate') as string;
        const endDateStr = formData.get('endDate') as string;

        const startDate = startDateStr ? new Date(startDateStr) : null;
        const endDate = endDateStr ? new Date(endDateStr) : null;

        if (startDate && endDate) {
          // Clamp both dates to bounds
          const clampedStartDate =
            startDate < min ? min : startDate > max ? max : startDate;

          const clampedEndDate =
            endDate < min ? min : endDate > max ? max : endDate;

          // Ensure start <= end
          const finalStartDate =
            clampedStartDate > clampedEndDate
              ? clampedEndDate
              : clampedStartDate;
          const finalEndDate =
            clampedEndDate < finalStartDate ? finalStartDate : clampedEndDate;

          onSubmit(finalStartDate, finalEndDate);
        }
      }}
      className="flex-container flex-container--vertical"
      style={{ gap: '2px' }}
    >
      <input
        type="date"
        name="startDate"
        min={str(min)}
        max={str(max)}
        defaultValue={str(initStartDate) || str(min)}
      />
      <input
        type="date"
        name="endDate"
        min={str(min)}
        max={str(max)}
        defaultValue={str(initEndDate) || str(max)}
      />
      <button type="submit">Apply</button>
    </form>
  );
};
