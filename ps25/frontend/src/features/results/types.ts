export type ResultUrgency = 'general' | 'time_sensitive' | 'urgent' | 'low' | 'medium' | 'high'

export type ProtectionClaim = {
  text: string
  source?: {
    title: string
    section?: string | null
    jurisdictionState?: "Maharashtra" | null
    sourceUrl?: string
    effectiveDate?: string | null
    versionLabel?: string | null
  } | null
}

export type NextStep = {
  title: string
  description: string
  source?: {
    title: string
    section?: string | null
    jurisdictionState?: "Maharashtra" | null
    sourceUrl?: string
    effectiveDate?: string | null
    versionLabel?: string | null
  } | null
}

export type OfficialResource = {
  name: string
  description?: string
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
  possibleIssues: string[]
  actor?: string | null
  jurisdictionState?: "Maharashtra" | null
  urgency: ResultUrgency
  urgencyMessage: string
  whatMayProtectYou: ProtectionClaim[]
  evidenceChecklist: string[]
  nextSteps: NextStep[]
  officialResources: OfficialResource[]
  legalAid: LegalAid | null
  disclaimer: string
}