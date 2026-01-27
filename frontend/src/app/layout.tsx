import { AuthProvider } from '../contexts/AuthContext'
import { ThemeProvider } from 'next-themes'
import { Toaster } from '../components/ui/sonner'
import { KeepAlivePing } from '../components/KeepAlivePing'
import '@/app/styles/globals.css'

export const metadata = {
  title: 'Todoer - Be Productive',
  description: 'Manage your tasks efficiently',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class">
          <KeepAlivePing />
          <AuthProvider>{children}</AuthProvider>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
