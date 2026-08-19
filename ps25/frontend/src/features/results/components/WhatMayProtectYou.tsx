import type { ProtectionClaim } from "../types"

type WhatMayProtectYouProps = {
  claims: ProtectionClaim[]
}

export default function WhatMayProtectYou({
  claims,
}: WhatMayProtectYouProps) {
  if (!claims || claims.length === 0) {
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
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            What May Protect You
          </h2>
          <p className="text-xs text-muted-foreground">
            Legal protections and statutory provisions relevant to your situation
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {claims.map((claim, index) => (
          <div
            key={index}
            className="rounded-lg border border-border/70 bg-muted/20 p-4 transition-colors hover:bg-muted/40"
          >
            <p className="text-sm sm:text-base leading-relaxed text-foreground font-medium">
              {claim.text}
            </p>
            {claim.source && claim.source.title && (
              <div className="mt-2.5 flex flex-wrap items-center gap-2 pt-1 border-t border-border/40 text-xs text-muted-foreground">
                <span className="font-medium text-foreground">
                  {claim.source.title}
                </span>
                {claim.source.section && (
                  <span className="inline-flex items-center rounded bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                    Section {claim.source.section}
                  </span>
                )}
                {claim.source.jurisdictionState && (
                  <span className="inline-flex items-center rounded bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                    {claim.source.jurisdictionState}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
