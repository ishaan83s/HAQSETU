import { useState } from "react"
import type { OfficialResource } from "../types"

type OfficialResourcesProps = {
  resources: OfficialResource[]
}

export default function OfficialResources({
  resources,
}: OfficialResourcesProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (!resources || resources.length === 0) {
    return null
  }

  return (
    <section className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden transition-all">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full flex items-center justify-between p-5 sm:p-6 text-left hover:bg-muted/20 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2.5">
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
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
              <path d="M6 6h10" />
              <path d="M6 10h10" />
            </svg>
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-semibold tracking-tight text-foreground flex items-center gap-2">
              Official Legal Sources
              <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                {resources.length}
              </span>
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Authoritative acts and statutory references cited in this guidance
            </p>
          </div>
        </div>

        <div className="text-muted-foreground pl-3">
          <svg
            className={`h-5 w-5 transform transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="px-5 pb-5 sm:px-6 sm:pb-6 pt-1 border-t border-border/50">
          <div className="grid gap-3 sm:grid-cols-2 mt-3">
            {resources.map((resource, index) => (
              <div
                key={`${resource.name}-${resource.section || index}`}
                className="flex flex-col justify-between rounded-lg border border-border/70 bg-muted/20 p-4 transition-all hover:bg-muted/40"
              >
                <div className="space-y-1.5 mb-3">
                  <h3 className="text-sm font-semibold tracking-tight text-foreground">
                    {resource.name}
                  </h3>
                  {(resource.section || resource.jurisdictionState || resource.versionLabel || resource.effectiveDate) && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                      {resource.section && (
                        <span className="inline-flex items-center rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                          Section {resource.section}
                        </span>
                      )}
                      {resource.jurisdictionState && (
                        <span className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                          {resource.jurisdictionState}
                        </span>
                      )}
                      {resource.versionLabel && (
                        <span className="inline-flex items-center rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                          {resource.versionLabel}
                        </span>
                      )}
                      {resource.effectiveDate && (
                        <span className="inline-flex items-center rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                          Eff. {resource.effectiveDate}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {resource.url ? (
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center justify-between rounded-md border border-border bg-background px-3 py-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    <span>View Official Text</span>
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
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}