'use client'

const TIME_SLOTS = [
  { value: 6, label: '6 AM' },
  { value: 8, label: '8 AM' },
  { value: 10, label: '10 AM' },
  { value: 12, label: '12 PM' },
  { value: 14, label: '2 PM' },
  { value: 16, label: '4 PM' },
  { value: 18, label: '6 PM' },
  { value: 20, label: '8 PM' },
]

export default function TimePicker({
  value,
  onChange,
  disabled,
}: {
  value: number
  onChange: (hour: number) => void
  disabled?: boolean
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      disabled={disabled}
      className="text-sm border border-gray-200 rounded-md px-2 py-1 bg-white text-gray-700 disabled:opacity-50"
    >
      {TIME_SLOTS.map((slot) => (
        <option key={slot.value} value={slot.value}>
          {slot.label}
        </option>
      ))}
    </select>
  )
}
