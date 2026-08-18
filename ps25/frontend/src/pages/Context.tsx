import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { updateUserContext } from "@/lib/context"

function Context() {
  const navigate = useNavigate()

  const [state, setState] = useState("")
  const [roleCategory, setRoleCategory] = useState("")
  const [vulnerabilityTags, setVulnerabilityTags] = useState<string[]>([])

  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const toggleVulnerabilityTag = (tag: string) => {
    setError("")
    setVulnerabilityTags((currentTags) =>
      currentTags.includes(tag)
        ? currentTags.filter((currentTag) => currentTag !== tag)
        : [...currentTags, tag],
    )
  }

  const handleSkip = () => {
    navigate("/incident")
  }

  const handleContinue = async () => {
    if (isLoading) return

    setError("")
    setIsLoading(true)

    try {
      const response = await updateUserContext({
        state: state || undefined,
        roleCategory: roleCategory || undefined,
        vulnerabilityTags:
          vulnerabilityTags.length > 0 ? vulnerabilityTags : undefined,
      })

      if (!response.success || !response.data?.saved) {
        setError(
          response.error?.message ??
            "Unable to save your context. Please try again.",
        )
        return
      }

      navigate("/incident")
    } catch {
      setError(
        "Unable to connect to the server. Please try again.",
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            A little about you
          </h1>

          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            This information can help us give you more relevant guidance.
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            You can skip this step.
          </p>
        </div>

        <div className="space-y-6 rounded-xl border bg-card p-6 shadow-sm">
          {/* State */}
          <div className="space-y-2">
            <label
              htmlFor="state"
              className="text-sm font-medium"
            >
              State
            </label>

            <select
              id="state"
              value={state}
              onChange={(event) => {
                setState(event.target.value)
                setError("")
              }}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select your state</option>
              <option value="Maharashtra">Maharashtra</option>
              <option value="Delhi">Delhi</option>
              <option value="Karnataka">Karnataka</option>
              <option value="Gujarat">Gujarat</option>
              <option value="Uttar Pradesh">Uttar Pradesh</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* Role */}
          <div className="space-y-2">
            <label
              htmlFor="role"
              className="text-sm font-medium"
            >
              What best describes you?
            </label>

            <select
              id="role"
              value={roleCategory}
              onChange={(event) => {
                setRoleCategory(event.target.value)
                setError("")
              }}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select your role</option>
              <option value="worker">Worker</option>
              <option value="student">Student</option>
              <option value="tenant">Tenant</option>
              <option value="employer">Employer</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Vulnerability tags */}
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium">
                Anything that may be relevant?
              </p>

              <p className="mt-1 text-xs text-muted-foreground">
                Select all that apply. This is optional.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {[
                ["gig_worker", "Gig worker"],
                ["migrant_worker", "Migrant worker"],
                ["person_with_disability", "Person with disability"],
                ["senior_citizen", "Senior citizen"],
              ].map(([value, label]) => {
                const selected = vulnerabilityTags.includes(value)

                return (
                  <button
                    key={value}
                    type="button"
                    onClick={() => toggleVulnerabilityTag(value)}
                    className={`rounded-full border px-3 py-2 text-sm font-medium transition-all ${
                      selected
                        ? "border-black bg-black text-white"
                        : "border-gray-300 bg-white text-black hover:bg-gray-100"
                    }`}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive">
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="space-y-3 pt-2">
            <button
              type="button"
              onClick={handleContinue}
              disabled={isLoading}
              className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? "Saving..." : "Continue"}
            </button>

            <button
              type="button"
              onClick={handleSkip}
              disabled={isLoading}
              className="w-full rounded-md border px-4 py-2.5 text-sm font-medium transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
            >
              Skip for now
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Context