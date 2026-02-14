import type { Metadata } from 'next'
import { Analytics } from '@vercel/analytics/next'
import { Geist } from 'next/font/google'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import './globals.css'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL('https://replaypub.vercel.app'),
  title: {
    default: 'Replay — Great blogs, delivered over time',
    template: '%s | Replay',
  },
  description: 'Subscribe to classic blog archives and receive posts as a drip email series.',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'Replay',
  },
  twitter: {
    card: 'summary',
  },
  alternates: {
    canonical: '/',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="light bg-white">
      <body className={`${geist.className} min-h-screen flex flex-col bg-white text-gray-900`}>
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
        <Analytics />
      </body>
    </html>
  )
}
