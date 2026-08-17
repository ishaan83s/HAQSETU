import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"

import { requestOtp, verifyOtp } from "@/lib/auth"

function Login() {
  const navigate = useNavigate()

  const [phoneNumber, setPhoneNumber] = useState("")
  const [otp, setOtp] = useState("")
  const [otpSent, setOtpSent] = useState(false)

  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handlePhoneSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setError("")

    const digits = phoneNumber.replace(/\D/g, "")

    if (digits.length !== 10) {
      setError("Please enter a valid 10-digit mobile number.")
      return
    }

    setIsLoading(true)

    try {
      const response = await requestOtp(`+91${digits}`)

      if (!response.success || !response.data?.otpSent) {
        setError(
          response.error?.message ??
            "Unable to send OTP. Please try again.",
        )
        return
      }

      setOtpSent(true)
    } catch {
      setError(
        "Unable to connect to the server. Please try again.",
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleOtpSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setError("")

    if (otp.length !== 6) {
      setError("Please enter the 6-digit OTP.")
      return
    }

    setIsLoading(true)

    try {
      const digits = phoneNumber.replace(/\D/g, "")
      const response = await verifyOtp(`+91${digits}`, otp)

      if (!response.success || !response.data) {
        setError(
          response.error?.message ??
            "Invalid OTP. Please try again.",
        )
        return
      }

      localStorage.setItem("ps25_token", response.data.token)
      localStorage.setItem("userId", response.data.userId)

      navigate("/context")
    } catch {
      setError(
        "Unable to connect to the server. Please try again.",
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">
            HAQSETU
          </h1>

          <p className="mt-3 text-muted-foreground">
            Legal awareness made accessible
          </p>
        </div>

        <div className="rounded-xl border bg-card p-6 shadow-sm">
          {!otpSent ? (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-semibold">
                  Welcome
                </h2>

                <p className="mt-2 text-sm text-muted-foreground">
                  Enter your mobile number to continue.
                </p>
              </div>

              <form
                onSubmit={handlePhoneSubmit}
                className="space-y-5"
              >
                <div className="space-y-2">
                  <label
                    htmlFor="phone"
                    className="text-sm font-medium"
                  >
                    Mobile number
                  </label>

                  <div className="flex">
                    <div className="flex items-center rounded-l-md border border-r-0 bg-muted px-3 text-sm">
                      +91
                    </div>

                    <input
                      id="phone"
                      type="tel"
                      inputMode="numeric"
                      maxLength={10}
                      placeholder="Enter 10-digit number"
                      value={phoneNumber}
                      onChange={(event) => {
                        setPhoneNumber(
                          event.target.value.replace(/\D/g, ""),
                        )
                        setError("")
                      }}
                      className="flex-1 rounded-r-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>

                  {error && (
                    <p className="text-sm text-destructive">
                      {error}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isLoading ? "Sending OTP..." : "Send OTP"}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-semibold">
                  Verify your number
                </h2>

                <p className="mt-2 text-sm text-muted-foreground">
                  Enter the 6-digit OTP sent to +91{" "}
                  {phoneNumber}
                </p>
              </div>

              <form
                onSubmit={handleOtpSubmit}
                className="space-y-5"
              >
                <div className="space-y-2">
                  <label
                    htmlFor="otp"
                    className="text-sm font-medium"
                  >
                    OTP
                  </label>

                  <input
                    id="otp"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    placeholder="Enter 6-digit OTP"
                    value={otp}
                    onChange={(event) => {
                      setOtp(
                        event.target.value.replace(/\D/g, ""),
                      )
                      setError("")
                    }}
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm tracking-[0.3em] outline-none focus:ring-2 focus:ring-ring"
                  />

                  {error && (
                    <p className="text-sm text-destructive">
                      {error}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isLoading ? "Verifying..." : "Verify OTP"}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setOtpSent(false)
                    setOtp("")
                    setError("")
                  }}
                  className="w-full text-sm text-muted-foreground hover:text-foreground"
                >
                  Change mobile number
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-xs text-muted-foreground">
          By continuing, you agree to use HAQSETU for legal
          awareness and guidance.
        </p>
      </div>
    </div>
  )
}

export default Login