import { useState, type ReactNode } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import AppShell from '@/components/AppShell'
import { Button } from '@/components/ui/button'
import { mockResult, sampleScenarios } from './mockResult'
import type { LegalAwarenessResult } from './types'
import UrgencyBanner from './components/UrgencyBanner'
import EvidenceChecklist from './components/EvidenceChecklist'
import NextStepsList from './components/NextStepsList'
import OfficialResources from './components/OfficialResources'

type ResultSectionProps = {
  title: string
  subtitle?: string
  icon?: ReactNode
  children: ReactNode
}

function ResultSection({
  title,
  subtitle,
  icon,
  children,
}: ResultSectionProps) {
  return (
    <section className="rounded-xl border bg-card p-5 sm:p-6 text-card-foreground shadow-sm">
      <div className="flex items-center gap-2.5 mb-3">
        {icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
        )}
        <div>
          <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
      </div>
      {children}
    </section>
  )
}

export default function ResultsPage() {
  const navigate = useNavigate()
  const { incidentId } = useParams<{ incidentId?: string }>()
  const location = useLocation()

  // State to support dynamic incident results and interactive demo scenarios
  const [selectedScenarioKey, setSelectedScenarioKey] =
    useState<string>('wage_nonpayment')

  const passedResult = (location.state as { result?: LegalAwarenessResult })
    ?.result

  const activeResult: LegalAwarenessResult =
    passedResult || sampleScenarios[selectedScenarioKey]?.data || mockResult

  return (
    <AppShell>
      <div className="space-y-6 pb-12">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
                HAQSETU Legal Awareness
              </span>
              {incidentId && (
                <span className="inline-flex items-center rounded-full border border-border bg-muted/60 px-2.5 py-0.5 text-xs font-medium text-foreground">
                  Case ID: #{incidentId}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Here is your next-step guide
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Personalized legal awareness, evidence preservation, and verified
              resources.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="text-xs"
            >
              <svg
                className="mr-1.5 h-3.5 w-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="6 9 6 2 18 2 18 9" />
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                <rect width="12" height="8" x="6" y="14" />
              </svg>
              Print / Save
            </Button>
            <Button
              size="sm"
              onClick={() => navigate('/incident')}
              className="text-xs"
            >
              New Query
            </Button>
          </div>
        </div>

        {/* Interactive Scenario Switcher for Demo / SIH Testing */}
        {!passedResult && (
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border/70 bg-muted/20 p-2.5">
            <span className="text-xs font-medium text-muted-foreground mr-1">
              Sample Case Scenarios:
            </span>
            {Object.entries(sampleScenarios).map(([key, scenario]) => (
              <button
                key={key}
                onClick={() => setSelectedScenarioKey(key)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
                  selectedScenarioKey === key
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-background hover:bg-muted text-muted-foreground hover:text-foreground border border-border/60'
                }`}
              >
                {scenario.label}
              </button>
            ))}
          </div>
        )}

        {/* Urgency Alert Banner */}
        <UrgencyBanner
          urgency={activeResult.urgency}
          message={activeResult.urgencyMessage}
        />

        {/* What We Understood Section */}
        <ResultSection
          title="What We Understood"
          subtitle="Summary of your situation and potential legal considerations"
          icon={
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
          }
        >
          <div className="space-y-3 text-sm text-foreground/90">
            <div className="rounded-lg bg-muted/40 p-3.5 border border-border/50">
              <p className="font-medium text-foreground mb-1 text-xs uppercase tracking-wider text-muted-foreground">
                Incident Overview
              </p>
              <p className="leading-relaxed">{activeResult.incidentSummary}</p>
            </div>
            <div className="rounded-lg bg-muted/40 p-3.5 border border-border/50">
              <p className="font-medium text-foreground mb-1 text-xs uppercase tracking-wider text-muted-foreground">
                Key Considerations
              </p>
              <p className="leading-relaxed">{activeResult.possibleIssue}</p>
            </div>
          </div>
        </ResultSection>

        {/* Evidence Preservation Checklist */}
        <EvidenceChecklist items={activeResult.evidenceChecklist} />

        {/* Actionable Next Steps */}
        <NextStepsList steps={activeResult.nextSteps} />

        {/* Official Resources */}
        <OfficialResources resources={activeResult.officialResources} />

        {/* Legal Disclaimer */}
        <div className="rounded-xl border border-muted-foreground/20 bg-muted/30 p-4 text-xs leading-relaxed text-muted-foreground">
          <div className="flex items-start gap-2.5">
            <svg
              className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <p>
              <strong className="font-semibold text-foreground">
                Disclaimer:{' '}
              </strong>
              {activeResult.disclaimer}
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  )
}