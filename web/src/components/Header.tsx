'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'

export default function Header() {
  const [user, setUser] = useState<User | null>(null)
  const supabase = createClient()

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => setUser(user))

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  return (
    <header className="border-b border-gray-100">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-lg font-semibold text-gray-900">
          Replay
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/request" className="text-gray-600 hover:text-gray-900">
            Request a blog
          </Link>
          {user && (
            <Link
              href="/dashboard"
              className="bg-gray-900 text-white px-3 py-1.5 rounded-md hover:bg-gray-800"
            >
              Dashboard
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
