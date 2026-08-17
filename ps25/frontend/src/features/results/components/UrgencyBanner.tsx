import type { ResultUrgency } from '../types'

type UrgencyBannerProps = {
  urgency: ResultUrgency
  message: string
}

const urgencyConfig: Record<
  ResultUrgency,
  { label: string; badgeClass: string; containerClass: string }
> = {
  emergency: {
    label: 'Emergency Attention Required',
    badgeClass:
      'bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200 border-red-300',
    containerClass:
      'border-red-200 bg-red-50/70 text-red-950 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200',
  },
  high: {
    label: 'High Urgency — Act Promptly',
    badgeClass:
      'bg-amber-100 text-amber-900 dark:bg-amber-900/60 dark:text-amber-200 border-amber-300',
    containerClass:
      'border-amber-200 bg-amber-50/70 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200',
  },
  medium: {
    label: 'Moderate Urgency',
    badgeClass:
      'bg-blue-100 text-blue-900 dark:bg-blue-900/60 dark:text-blue-200 border-blue-300',
    containerClass:
      'border-blue-200 bg-blue-50/70 text-blue-950 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200',
  },
  low: {
    label: 'Standard Awareness',
    badgeClass:
      'bg-emerald-100 text-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-200 border-emerald-300',
    containerClass:
      'border-emerald-200 bg-emerald-50/70 text-emerald-950 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200',
  },
}

export default function UrgencyBanner({
  urgency,
  message,
}: UrgencyBannerProps) {
  const config = urgencyConfig[urgency] || urgencyConfig.high

  return (
    <section
      aria-label="Urgency notice"
      className={`rounded-xl border p-4 sm:p-5 transition-all shadow-sm ${config.containerClass}`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">
          <svg
            className="h-5 w-5 text-current opacity-90"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${config.badgeClass}`}
            >
              {config.label}
            </span>
          </div>
          <p className="text-sm sm:text-base leading-relaxed font-medium">
            {message}
          </p>
        </div>
      </div>
    </section>
  )
}