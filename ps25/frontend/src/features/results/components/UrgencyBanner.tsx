import type { ResultUrgency } from '../types'

type UrgencyBannerProps = {
  urgency: ResultUrgency
  message: string
}

const urgencyLabel: Record<ResultUrgency, string> = {
  low: 'Low urgency',
  medium: 'Medium urgency',
  high: 'High urgency',
  emergency: 'Emergency',
}

export default function UrgencyBanner({
  urgency,
  message,
}: UrgencyBannerProps) {
  return (
    <section aria-label="Urgency notice">
      <strong>{urgencyLabel[urgency]}</strong>
      <p>{message}</p>
    </section>
  )
}