import { apiRequest } from "./api"

export type IncidentInputMode = "text" | "voice"
export type IncidentLanguage = "hi" | "en"

export interface CreateIncidentRequest {
  inputMode: IncidentInputMode
  language: IncidentLanguage
  text: string | null
  audioBase64: string | null
}

export interface CreateIncidentResponse {
  incidentId: string
}

export function createIncident(
  request: CreateIncidentRequest,
) {
  return apiRequest<CreateIncidentResponse>("/incidents", {
    method: "POST",
    body: JSON.stringify(request),
  })
} 