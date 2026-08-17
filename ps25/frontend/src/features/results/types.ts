export type ResultUrgency = 'low' | 'medium' | 'high' | 'emergency'

export type NextStep = {
  title: string
  description: string
}

export type OfficialResource = {
  name: string
  description: string
  url: string
}

export type LegalAwarenessResult = {
  incidentSummary: string
  possibleIssue: string
  urgency: ResultUrgency
  urgencyMessage: string
  evidenceChecklist: string[]
  nextSteps: NextStep[]
  officialResources: OfficialResource[]
  disclaimer: string
}