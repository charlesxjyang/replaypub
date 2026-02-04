export default function ProgressBar({
  current,
  total,
}: {
  current: number
  total: number
}) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Post {current} of {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="bg-gray-200 rounded-full h-1.5 w-full">
        <div
          className="bg-blue-600 rounded-full h-1.5 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
