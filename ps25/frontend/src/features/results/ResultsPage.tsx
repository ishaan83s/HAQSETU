import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AppShell from "@/components/AppShell"
import { Button } from "@/components/ui/button"
import { getIncident } from "@/lib/incidents"
import { adaptIncidentResult } from "./incidentAdapter"
import type { LegalAwarenessResult } from "./types"
import UrgencyBanner from "./components/UrgencyBanner"
import WhatMayProtectYou from "./components/WhatMayProtectYou"
import EvidenceChecklist from "./components/EvidenceChecklist"
import NextStepsList from "./components/NextStepsList"
import OfficialResources from "./components/OfficialResources"
import LegalAidCard from "./components/LegalAidCard"

export default function ResultsPage() {
  const navigate = useNavigate()
  const { incidentId } = useParams<{ incidentId?: string }>()
  const [result, setResult] = useState<LegalAwarenessResult | null>(null)
  const [isLoading, setIsLoading] = useState(Boolean(incidentId))
  const [error, setError] = useState("")

  useEffect(() => {
    if (!incidentId) {
      return
    }

    const currentIncidentId = incidentId
    let cancelled = false

    async function loadIncident() {
      setIsLoading(true)
      setError("")

      try {
        const response = await getIncident(currentIncidentId)

        if (!response.success || !response.data) {
          if (!cancelled) {
            setError(
              response.error?.message ??
                "We couldn't load your result. Please try again.",
            )
          }
          return
        }

        if (!cancelled) {
          setResult(adaptIncidentResult(response.data))
        }
      } catch {
        if (!cancelled) {
          setError("We couldn't connect to the service. Please try again.")
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadIncident()

    return () => {
      cancelled = true
    }
  }, [incidentId])

  const effectiveError = !incidentId ? "We couldn't find this incident." : error
  const activeResult = result

  if (isLoading && incidentId) {
    return (
      <AppShell>
        <div className="flex min-h-[60vh] items-center justify-center px-4">
          <div className="text-center">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <svg
                className="h-6 w-6 animate-pulse"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <h1 className="text-xl sm:text-2xl font-semibold text-foreground">
              Loading your guidance
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Please wait while we load your legal-awareness guidance.
            </p>
          </div>
        </div>
      </AppShell>
    )
  }

  if (effectiveError || !activeResult) {
    return (
      <AppShell>
        <div className="flex min-h-[60vh] items-center justify-center px-4">
          <div className="w-full max-w-md text-center rounded-xl border border-border bg-card p-6 shadow-sm">
            <h1 className="text-xl sm:text-2xl font-semibold text-foreground">
              We couldn't load your result
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {effectiveError || "Please try again."}
            </p>
            <Button className="mt-6" onClick={() => navigate("/incident")}>
              Start a New Query
            </Button>
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 sm:space-y-8 pb-16">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-5">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="inline-flex items-center rounded-md bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
                HAQSETU Guidance
              </span>
              {activeResult.possibleIssues.map((issue) => (
                <span
                  key={issue}
                  className="inline-flex items-center rounded-md border border-border bg-muted/40 px-2.5 py-0.5 text-xs font-medium text-muted-foreground"
                >
                  {issue}
                </span>
              ))}
              {activeResult.jurisdictionState && (
                <span className="inline-flex items-center rounded-md border border-border bg-muted/40 px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                  {activeResult.jurisdictionState}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Here's what we found
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Plain-language summary of your situation, relevant legal provisions, and recommended actions.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              size="sm"
              onClick={() => navigate("/incident")}
              className="text-xs"
            >
              New Query
            </Button>
          </div>
        </div>

        {/* Urgency Alert Banner (if urgent or time-sensitive) */}
        {(activeResult.urgency === "urgent" ||
          activeResult.urgency === "time_sensitive" ||
          activeResult.urgency === "high" ||
          activeResult.urgency === "medium") && (
          <UrgencyBanner
            urgency={activeResult.urgency}
            message={activeResult.urgencyMessage}
          />
        )}

        {/* What May Be Happening */}
        {activeResult.incidentSummary && (
          <section className="rounded-xl border bg-card p-5 sm:p-6 text-card-foreground shadow-sm">
            <div className="flex items-center gap-2.5 mb-3.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold tracking-tight">
                  What May Be Happening
                </h2>
                <p className="text-xs text-muted-foreground">
                  Summary of the situation and primary legal assessment
                </p>
              </div>
            </div>

            <div className="rounded-lg bg-muted/30 p-4 border border-border/60">
              <p className="text-sm sm:text-base leading-relaxed text-foreground font-normal whitespace-pre-line">
                {activeResult.incidentSummary}
              </p>
            </div>
          </section>
        )}

        {/* What May Protect You */}
        <WhatMayProtectYou claims={activeResult.whatMayProtectYou} />

        {/* Evidence Preservation Checklist */}
        <EvidenceChecklist items={activeResult.evidenceChecklist} />

        {/* Actionable Next Steps */}
        <NextStepsList steps={activeResult.nextSteps} />

        {/* Official Legal Sources (Progressively Disclosed) */}
        <OfficialResources resources={activeResult.officialResources} />

        {/* Connect to Legal Aid */}
        <LegalAidCard legalAid={activeResult.legalAid} />

        {/* Legal Disclaimer */}
        <div className="rounded-xl border border-border/80 bg-muted/20 p-4 text-xs leading-relaxed text-muted-foreground">
          <p>
            <strong className="font-semibold text-foreground">
              Disclaimer:{" "}
            </strong>
            {activeResult.disclaimer}
          </p>
        </div>
      </div>
    </AppShell>
  )
}