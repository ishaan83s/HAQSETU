import type { ReactNode } from "react"

interface AppShellProps {
  children: ReactNode
}

function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-3xl items-center px-4 sm:px-6">
          <span className="text-lg font-semibold tracking-tight">
            HAQSETU
          </span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
        {children}
      </main>
    </div>
  )
}

export default AppShell