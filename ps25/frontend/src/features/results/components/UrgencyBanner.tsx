import type { ResultUrgency } from "../types"

type UrgencyBannerProps = {
  urgency: ResultUrgency
  message: string
}

const urgencyConfig: Record<
  string,
  { label: string; badgeClass: string; containerClass: string }
> = {
  urgent: {
    label: "Prompt Attention Recommended",
    badgeClass:
      "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950/60 dark:text-amber-200 dark:border-amber-800",
    containerClass:
      "border-amber-200 bg-amber-50/60 text-amber-950 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-200",
  },
  high: {
    label: "Prompt Attention Recommended",
    badgeClass:
      "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950/60 dark:text-amber-200 dark:border-amber-800",
    containerClass:
      "border-amber-200 bg-amber-50/60 text-amber-950 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-200",
  },
  time_sensitive: {
    label: "Time-Sensitive Situation",
    badgeClass:
      "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950/60 dark:text-blue-200 dark:border-blue-800",
    containerClass:
      "border-blue-200 bg-blue-50/60 text-blue-950 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-200",
  },
  medium: {
    label: "Time-Sensitive Situation",
    badgeClass:
      "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950/60 dark:text-blue-200 dark:border-blue-800",
    containerClass:
      "border-blue-200 bg-blue-50/60 text-blue-950 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-200",
  },
  general: {
    label: "General Awareness",
    badgeClass:
      "bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700",
    containerClass:
      "border-slate-200 bg-slate-50/70 text-slate-900 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-200",
  },
  low: {
    label: "General Awareness",
    badgeClass:
      "bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700",
    containerClass:
      "border-slate-200 bg-slate-50/70 text-slate-900 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-200",
  },
}

export default function UrgencyBanner({
  urgency,
  message,
}: UrgencyBannerProps) {
  const config = urgencyConfig[urgency] || urgencyConfig.general

  return (
    <section
      aria-label="Urgency notice"
      className={`rounded-xl border p-4 sm:p-5 transition-all shadow-sm ${config.containerClass}`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">
          <svg
            className="h-5 w-5 text-current opacity-85"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
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