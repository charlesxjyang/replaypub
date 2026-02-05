import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Request a Blog',
  description: 'Submit and vote for blogs you want to see on Replay.',
  alternates: { canonical: '/request' },
}

export default function RequestLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
