import type { LegalAid } from "../types"

type LegalAidCardProps = {
  legalAid: LegalAid
}

export default function LegalAidCard({
  legalAid,
}: LegalAidCardProps) {
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
            <path d="M12 3v18" />
            <path d="M5 6h14" />
            <path d="M7 6l-3 7h6L7 6Z" />
            <path d="M17 6l-3 7h6l-3-7Z" />
            <path d="M4 18h16" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Legal Aid
          </h2>
          <p className="text-xs text-muted-foreground">
            A legal-services contact associated with this guidance
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-border/70 bg-muted/20 p-4">
        <h3 className="text-sm font-semibold text-foreground">
          {legalAid.name}
        </h3>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
          {legalAid.contactInfo}
        </p>
      </div>
    </section>
  )
}
