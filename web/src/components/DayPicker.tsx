'use client'

const DAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'] // 0=Sun through 6=Sat

export default function DayPicker({
  value,
  onChange,
  disabled,
}: {
  value: number | null
  onChange: (day: number | null) => void
  disabled?: boolean
}) {
  return (
    <div className="flex gap-1">
      {DAYS.map((label, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onChange(value === i ? null : i)}
          disabled={disabled}
          className={`w-8 h-8 rounded-full text-xs font-medium transition-colors disabled:opacity-50 ${
            value === i
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
