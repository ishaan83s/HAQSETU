import type { NextStep } from '../types'

type NextStepsListProps = {
  steps: NextStep[]
}

export default function NextStepsList({ steps }: NextStepsListProps) {
  return (
    <section>
      <h2>What you can do next</h2>

      <ol>
        {steps.map((step) => (
          <li key={step.title}>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}