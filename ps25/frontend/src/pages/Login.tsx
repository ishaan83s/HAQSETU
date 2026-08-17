import { useNavigate } from "react-router-dom"
import AppShell from "@/components/AppShell"
import { Button } from "@/components/ui/button"

function Login() {
  const navigate = useNavigate()

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center text-center py-12 space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">Citizen Authentication</h1>
        <p className="text-muted-foreground max-w-md text-sm">
          Authentication module placeholder. Click below to proceed directly to the Intake or Results page.
        </p>
        <div className="flex items-center gap-3">
          <Button onClick={() => navigate("/incident")}>
            Go to Incident Intake
          </Button>
          <Button variant="outline" onClick={() => navigate("/results")}>
            View Results Demo
          </Button>
        </div>
      </div>
    </AppShell>
  )
}

export default Login