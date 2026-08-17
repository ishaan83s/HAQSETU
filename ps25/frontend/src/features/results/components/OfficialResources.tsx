import type { OfficialResource } from '../types'

type OfficialResourcesProps = {
  resources: OfficialResource[]
}

export default function OfficialResources({
  resources,
}: OfficialResourcesProps) {
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
            <path d="M3 21h18" />
            <path d="M5 21V7l8-4v18" />
            <path d="M19 21V11l-6-4" />
            <path d="M9 9v.01" />
            <path d="M9 12v.01" />
            <path d="M9 15v.01" />
            <path d="M9 18v.01" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Official Authorities & Legal Aid
          </h2>
          <p className="text-xs text-muted-foreground">
            Verified government helplines and legal assistance portals
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {resources.map((resource) => (
          <div
            key={resource.url}
            className="flex flex-col justify-between rounded-lg border border-border/70 bg-muted/20 p-4 transition-all hover:border-primary/50 hover:bg-muted/40"
          >
            <div className="space-y-1.5 mb-4">
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                <h3 className="text-sm font-semibold tracking-tight text-foreground">
                  {resource.name}
                </h3>
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {resource.description}
              </p>
            </div>

            <a
              href={resource.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-xs font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <span>Visit Official Portal</span>
              <svg
                className="h-3.5 w-3.5 opacity-70"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </a>
          </div>
        ))}
      </div>
    </section>
  )
}