import { useRef, useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"

import { createIncident } from "@/lib/incidents"

type InputMode = "text" | "voice"

function Incident() {
  const navigate = useNavigate()

  const [language, setLanguage] = useState<"en" | "hi">("en")
  const [inputMode, setInputMode] = useState<InputMode>("text")

  const [incidentText, setIncidentText] = useState("")
  const [audioBase64, setAudioBase64] = useState<string | null>(null)

  const [isRecording, setIsRecording] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const startRecording = async () => {
    setError("")

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      })

      audioChunksRef.current = []

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      })

      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType,
        })

        const reader = new FileReader()

        reader.onloadend = () => {
          const result = reader.result

          if (typeof result === "string") {
            const base64 = result.split(",")[1]

            if (base64) {
              setAudioBase64(base64)
            }
          }
        }

        reader.readAsDataURL(audioBlob)

        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch {
      setError(
        "Microphone access was denied or is not available.",
      )
    }
  }

  const stopRecording = () => {
    const mediaRecorder = mediaRecorderRef.current

    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop()
      setIsRecording(false)
    }
  }

  const handleModeChange = (mode: InputMode) => {
    setInputMode(mode)
    setError("")

    if (mode === "text") {
      setAudioBase64(null)
    } else {
      setIncidentText("")
    }
  }

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setError("")

    if (inputMode === "text") {
      if (!incidentText.trim()) {
        setError("Please describe what happened.")
        return
      }
    }

    if (inputMode === "voice" && !audioBase64) {
      setError("Please record your situation before submitting.")
      return
    }

    setIsSubmitting(true)

    try {
      const response = await createIncident({
        inputMode,
        language,
        text:
          inputMode === "text"
            ? incidentText.trim()
            : null,
        audioBase64:
          inputMode === "voice"
            ? audioBase64
            : null,
      })

      if (!response.success || !response.data) {
        setError(
          response.error?.message ??
          "We couldn't process your request. Please try again.",
        )
        return
      }

      if ("emptyTranscription" in response.data && response.data.emptyTranscription) {
        setError(
          "We could not detect clear speech in your recording. Please try speaking again or use text input.",
        )
        return
      }

      if (!response.data.incidentId) {
        setError("We couldn't create the incident. Please try again.")
        return
      }

      navigate(`/result/${response.data.incidentId}`)
    } catch {
      setError(
        "We couldn't connect to the service. Please try again.",
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isSubmitting) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="w-full max-w-md text-center">
          <div className="mb-6 text-4xl">⏳</div>

          <h1 className="text-2xl font-semibold">
            Understanding your situation
          </h1>

          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Please wait while we process what you shared.
          </p>

          <div className="mx-auto mt-6 h-2 w-full max-w-xs overflow-hidden rounded-full bg-muted">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-primary" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <div className="w-full max-w-2xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            Tell us what happened
          </h1>

          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Describe your situation in your own words. We&apos;ll
            help you understand what may be happening and what you
            can do next.
          </p>
        </div>

        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Language */}
            <div className="space-y-3">
              <p className="text-sm font-medium">
                Preferred language
              </p>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setLanguage("en")}
                  disabled={isSubmitting}
                  className={`rounded-md border px-5 py-2 text-sm font-medium transition-all ${language === "en"
                    ? "border-black bg-black text-white"
                    : "border-gray-300 bg-white text-black hover:bg-gray-100"
                    }`}
                >
                  English
                </button>

                <button
                  type="button"
                  onClick={() => setLanguage("hi")}
                  disabled={isSubmitting}
                  className={`rounded-md border px-5 py-2 text-sm font-medium transition-all ${language === "hi"
                    ? "border-black bg-black text-white"
                    : "border-gray-300 bg-white text-black hover:bg-gray-100"
                    }`}
                >
                  हिंदी
                </button>
              </div>
            </div>

            {/* Input mode */}
            <div className="space-y-3">
              <p className="text-sm font-medium">
                How would you like to describe it?
              </p>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => handleModeChange("text")}
                  className={`rounded-md border px-5 py-2 text-sm font-medium transition-all ${inputMode === "text"
                    ? "border-black bg-black text-white"
                    : "border-gray-300 bg-white text-black hover:bg-gray-100"
                    }`}
                >
                  Write
                </button>

                <button
                  type="button"
                  onClick={() => handleModeChange("voice")}
                  className={`rounded-md border px-5 py-2 text-sm font-medium transition-all ${inputMode === "voice"
                    ? "border-black bg-black text-white"
                    : "border-gray-300 bg-white text-black hover:bg-gray-100"
                    }`}
                >
                  Voice
                </button>
              </div>
            </div>

            {/* Text input */}
            {inputMode === "text" && (
              <div className="space-y-2">
                <label
                  htmlFor="incident"
                  className="text-sm font-medium"
                >
                  What happened?
                </label>

                <textarea
                  id="incident"
                  value={incidentText}
                  onChange={(event) => {
                    setIncidentText(event.target.value)
                    setError("")
                  }}
                  placeholder="Describe what happened..."
                  rows={7}
                  maxLength={2000}
                  className="w-full resize-none rounded-md border bg-background px-3 py-3 text-sm leading-6 outline-none focus:ring-2 focus:ring-ring"
                />

                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>
                    You can describe the situation in your own words.
                  </span>

                  <span>{incidentText.length}/2000</span>
                </div>
              </div>
            )}

            {/* Voice input */}
            {inputMode === "voice" && (
              <div className="rounded-lg border p-6 text-center">
                <div className="mb-4">
                  <p className="text-sm font-medium">
                    Record your situation
                  </p>

                  <p className="mt-1 text-xs text-muted-foreground">
                    Speak clearly and describe what happened.
                  </p>
                </div>

                {!isRecording ? (
                  <button
                    type="button"
                    onClick={startRecording}
                    className="rounded-full border border-black bg-black px-6 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90"
                  >
                    Start recording
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="rounded-full border border-red-600 bg-red-600 px-6 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90"
                  >
                    Stop recording
                  </button>
                )}

                {isRecording && (
                  <p className="mt-4 text-sm font-medium">
                    🔴 Recording...
                  </p>
                )}

                {!isRecording && audioBase64 && (
                  <p className="mt-4 text-sm text-muted-foreground">
                    ✓ Recording ready
                  </p>
                )}
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3">
                <p className="text-sm text-red-700">
                  {error}
                </p>

                <button
                  type="button"
                  onClick={() => setError("")}
                  className="mt-2 text-sm font-medium text-red-800 underline"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isRecording}
              className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Get guidance
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Incident