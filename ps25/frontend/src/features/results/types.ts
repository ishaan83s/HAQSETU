export type ResultUrgency = 'low' | 'medium' | 'high' | 'emergency'

export type NextStep = {
  title: string
  description: string
}

export type OfficialResource = {
  name: string
  description: string
  url: string
  section?: string | null
  jurisdictionState?: "Maharashtra" | null
  effectiveDate?: string | null
  versionLabel?: string | null
}

export type LegalAid = {
  name: string
  contactInfo: string
}

export type LegalAwarenessResult = {
  incidentSummary: string
  possibleIssue: string
  urgency: ResultUrgency
  urgencyMessage: string
  evidenceChecklist: string[]
  nextSteps: NextStep[]
  officialResources: OfficialResource[]
  legalAid: LegalAid
  disclaimer: string
}