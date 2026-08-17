import type { ReactNode } from 'react'
import { mockResult } from './mockResult'
import UrgencyBanner from './components/UrgencyBanner'
import EvidenceChecklist from './components/EvidenceChecklist'
import NextStepsList from './components/NextStepsList'
import OfficialResources from './components/OfficialResources'

type ResultSectionProps = {
  title: string
  children: ReactNode
}

function ResultSection({ title, children }: ResultSectionProps) {
  return (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  )
}

export default function ResultsPage() {
  return (
    <main>
      <p>HAQSETU Legal Awareness Result</p>

      <h1>Here is a clear next-step guide</h1>

      <UrgencyBanner
        urgency={mockResult.urgency}
        message={mockResult.urgencyMessage}
      />

      <ResultSection title="What we understood">
        <p>{mockResult.incidentSummary}</p>
        <p>{mockResult.possibleIssue}</p>
      </ResultSection>

      <EvidenceChecklist items={mockResult.evidenceChecklist} />

      <NextStepsList steps={mockResult.nextSteps} />

      <OfficialResources resources={mockResult.officialResources} />

      <ResultSection title="Important">
        <p>{mockResult.disclaimer}</p>
      </ResultSection>
    </main>
  )
}