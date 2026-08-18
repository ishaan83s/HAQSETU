import { apiRequest } from "./api"

export type IncidentInputMode = "text" | "voice"
export type IncidentLanguage = "hi" | "en"

export interface CreateIncidentRequest {
  inputMode: IncidentInputMode
  language: IncidentLanguage
  text: string | null
  audioBase64: string | null
}

export interface EmptyTranscriptionPayload {
  emptyTranscription: true
  incidentId?: never
}

export type CreateIncidentResponse =
  | GetIncidentResponse
  | EmptyTranscriptionPayload

export function createIncident(
  request: CreateIncidentRequest,
) {
  return apiRequest<CreateIncidentResponse>("/incidents", {
    method: "POST",
    body: JSON.stringify(request),
  })
} 
export interface GetIncidentResponse {
  incidentId: string
  triage: {
    issues: Array<{
      type: string
    }>
    actor: string | null
    jurisdictionState: "Maharashtra" | null
    urgency: "general" | "time_sensitive" | "urgent"
    cards: {
      whatMayBeHappening: {
        text: string
      }
      whatMayProtectYou: Array<{
        text: string
        source: {
          title: string
          section: string | null
          jurisdictionState: "Maharashtra" | null
          sourceUrl: string
          effectiveDate: string | null
          versionLabel: string | null
        }
      }>
      evidenceToKeep: string[]
      whatYouCanDoNext: Array<{
        text: string
        source: {
          title: string
          section: string | null
          jurisdictionState: "Maharashtra" | null
          sourceUrl: string
          effectiveDate: string | null
          versionLabel: string | null
        }
      }>
      legalAid: {
        name: string
        contactInfo: string
      }
    }
  }
}

export function getIncident(incidentId: string) {
  return apiRequest<GetIncidentResponse>(`/incidents/${incidentId}`)
}
