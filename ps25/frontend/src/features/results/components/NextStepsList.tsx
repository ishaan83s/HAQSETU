import type { NextStep } from '../types'

type NextStepsListProps = {
  steps: NextStep[]
}

export default function NextStepsList({ steps }: NextStepsListProps) {
  return (
    <section className="rounded-xl border bg-card p-5 sm:p-6 text-card-foreground shadow-sm">
      <div className="flex items-center gap-2.5 mb-5">
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
            Recommended Action Steps
          </h2>
          <p className="text-xs text-muted-foreground">
            Follow these sequential steps to protect your rights
          </p>
        </div>
      </div>

      <ol className="space-y-3">
        {steps.map((step, idx) => (
          <li
            key={step.title}
            className="flex items-start gap-3.5 rounded-lg border border-border/60 bg-muted/20 p-4 transition-colors hover:border-primary/40 hover:bg-muted/50"
          >
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-sm">
              {idx + 1}
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold tracking-tight text-foreground">
                {step.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}