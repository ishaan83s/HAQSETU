const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

interface ApiError {
  code: string
  message: string
}

export interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: ApiError | null
}

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("ps25_token")

  const headers = new Headers(options?.headers)

  headers.set("Content-Type", "application/json")

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  const body = (await response.json()) as ApiResponse<T>

  return body
}