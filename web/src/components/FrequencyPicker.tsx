'use client'

const OPTIONS = [
  { value: 1, label: 'Daily' },
  { value: 3, label: 'Every 3 days' },
  { value: 7, label: 'Weekly' },
  { value: 14, label: 'Biweekly' },
]

export default function FrequencyPicker({
  value,
  onChange,
  disabled,
}: {
  value: number
  onChange: (days: number) => void
  disabled?: boolean
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      disabled={disabled}
      className="text-sm border border-gray-200 rounded-md px-2 py-1 bg-white text-gray-700 disabled:opacity-50"
    >
      {OPTIONS.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
