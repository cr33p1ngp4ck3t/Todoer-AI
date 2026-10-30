import { AuthProvider } from '../contexts/AuthContext'
import { ThemeProvider } from 'next-themes'
import { Toaster } from '../components/ui/sonner'
import { Analytics } from '@vercel/analytics/next'
import '@/app/styles/globals.css'

export const metadata = {
  title: 'Todoer AI — A little more clarity',
  description:
    'Plan your day, draft tasks with AI, and keep shared projects moving.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          <AuthProvider>{children}</AuthProvider>
          <Toaster />
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
