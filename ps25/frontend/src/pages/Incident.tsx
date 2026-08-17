import { useNavigate } from "react-router-dom"
import AppShell from "@/components/AppShell"
import { Button } from "@/components/ui/button"

function Incident() {
  const navigate = useNavigate()

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center text-center py-12 space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">Incident Intake Flow</h1>
        <p className="text-muted-foreground max-w-md text-sm">
          Phase 3 intake form is being connected. Click below to view the completed Phase 4 Legal Awareness Results.
        </p>
        <Button onClick={() => navigate("/results")} size="lg">
          Generate & View Results Guide →
        </Button>
      </div>
    </AppShell>
  )
}

export default Incident