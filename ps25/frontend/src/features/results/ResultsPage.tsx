import type { ReactNode } from 'react'

type ResultSectionProps = {
  title: string
  children: ReactNode
}

function ResultSection({ title, children }: ResultSectionProps) {
  return (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  )
}

export default function ResultsPage() {
  return (
    <main>
      <p>HAQSETU Legal Awareness Result</p>

      <h1>Here is a clear next-step guide</h1>

      <ResultSection title="What we understood">
        <p>
          You described a situation that may need legal awareness and support.
        </p>
      </ResultSection>

      <ResultSection title="What you can do next">
        <ol>
          <li>Keep any messages, documents, photos, or recordings safe.</li>
          <li>Write down dates, names, locations, and what happened.</li>
          <li>Contact an appropriate official service or legal-aid provider.</li>
        </ol>
      </ResultSection>

      <ResultSection title="Important">
        <p>
          HAQSETU provides legal awareness, not legal advice or representation.
        </p>
      </ResultSection>
    </main>
  )
}