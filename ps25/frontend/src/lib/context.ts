import { apiRequest } from "./api"

export interface UserContext {
  state?: string
  roleCategory?: string
  vulnerabilityTags?: string[]
}

interface UpdateContextResponse {
  saved: boolean
}

export function updateUserContext(context: UserContext) {
  return apiRequest<UpdateContextResponse>("/users/context", {
    method: "PUT",
    body: JSON.stringify(context),
  })
}