import type { LegalAid } from "../types"

type LegalAidCardProps = {
  legalAid: LegalAid | null | undefined
}

export default function LegalAidCard({
  legalAid,
}: LegalAidCardProps) {
  if (!legalAid || (!legalAid.name && !legalAid.contactInfo)) {
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
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Connect to Legal Aid
          </h2>
          <p className="text-xs text-muted-foreground">
            Free and institutional legal assistance options
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-border/70 bg-muted/20 p-4">
        {legalAid.name && (
          <h3 className="text-sm font-semibold text-foreground">
            {legalAid.name}
          </h3>
        )}
        {legalAid.contactInfo && (
          <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground font-medium">
            {legalAid.contactInfo}
          </p>
        )}
      </div>
    </section>
  )
}
