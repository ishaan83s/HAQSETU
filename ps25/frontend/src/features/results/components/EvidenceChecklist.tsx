type EvidenceChecklistProps = {
  items: string[]
}

export default function EvidenceChecklist({
  items,
}: EvidenceChecklistProps) {
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
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <path d="m9 15 2 2 4-4" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Evidence & Records to Keep Safe
          </h2>
          <p className="text-xs text-muted-foreground">
            Preserve originals and make backups of the following items
          </p>
        </div>
      </div>

      <ul className="space-y-2.5">
        {items.map((item, index) => (
          <li
            key={index}
            className="flex items-start gap-3 rounded-lg border border-border/60 bg-muted/30 p-3 transition-colors hover:bg-muted/60"
          >
            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <svg
                className="h-3 w-3"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span className="text-sm leading-relaxed text-foreground">
              {item}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}