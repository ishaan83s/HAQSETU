import type { NextStep } from "../types"

type NextStepsListProps = {
  steps: NextStep[]
}

export default function NextStepsList({ steps }: NextStepsListProps) {
  if (!steps || steps.length === 0) {
    return null
  }

  return (
    <section className="rounded-xl border bg-card p-5 sm:p-6 text-card-foreground shadow-sm">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            What You Can Do Next
          </h2>
          <p className="text-xs text-muted-foreground">
            Clear, actionable steps you can take to address this issue
          </p>
        </div>
      </div>

      <ol className="space-y-3">
        {steps.map((step, idx) => (
          <li
            key={idx}
            className="flex items-start gap-3.5 rounded-lg border border-border/70 bg-muted/20 p-4 transition-colors hover:bg-muted/40"
          >
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-sm mt-0.5">
              {idx + 1}
            </div>
            <div className="space-y-1">
              <p className="text-sm sm:text-base leading-relaxed text-foreground font-medium">
                {step.description}
              </p>
              {step.source && step.source.title && (
                <div className="mt-2 flex flex-wrap items-center gap-1.5 pt-1 text-xs text-muted-foreground">
                  <span>Reference: {step.source.title}</span>
                  {step.source.section && (
                    <span className="font-medium text-foreground">
                      (Section {step.source.section})
                    </span>
                  )}
                </div>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}