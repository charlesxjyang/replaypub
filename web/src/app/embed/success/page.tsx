import { Suspense } from 'react'
import SuccessContent from './success-content'

export default function SuccessPage() {
  return (
    <Suspense fallback={<p className="text-gray-500 text-center py-16">Loading...</p>}>
      <SuccessContent />
    </Suspense>
  )
}
