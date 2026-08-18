import { apiRequest } from "./api"

interface RequestOtpData {
  otpSent: boolean
}

interface VerifyOtpData {
  token: string
  userId: string
}

export function requestOtp(phoneNumber: string) {
  return apiRequest<RequestOtpData>("/auth/request-otp", {
    method: "POST",
    body: JSON.stringify({
      phoneNumber,
    }),
  })
}

export function verifyOtp(phoneNumber: string, otp: string) {
  return apiRequest<VerifyOtpData>("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({
      phoneNumber,
      otp,
    }),
  })
}