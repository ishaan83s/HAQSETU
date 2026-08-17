import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import AppShell from "@/components/AppShell"

function Onboarding() {
  const navigate = useNavigate()

  return (
    <AppShell>
      <section className="flex min-h-[calc(100vh-9rem)] flex-col items-center justify-center text-center">
        <div className="max-w-xl">
          <p className="mb-3 text-sm font-medium text-muted-foreground">
            Legal awareness made accessible
          </p>

          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            HAQSETU
          </h1>

          <p className="mx-auto mt-5 max-w-lg text-base leading-7 text-muted-foreground sm:text-lg">
            Tell us what happened. We’ll help you understand what may be
            happening and what you can do next.
          </p>

          <Button
            size="lg"
            className="mt-8"
            onClick={() => navigate("/login")}
          >
            Get started
          </Button>
        </div>
      </section>
    </AppShell>
  )
}

export default Onboarding