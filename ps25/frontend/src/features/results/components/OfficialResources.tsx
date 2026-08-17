import type { OfficialResource } from '../types'

type OfficialResourcesProps = {
  resources: OfficialResource[]
}

export default function OfficialResources({
  resources,
}: OfficialResourcesProps) {
  return (
    <section>
      <h2>Official help and resources</h2>

      <ul>
        {resources.map((resource) => (
          <li key={resource.url}>
            <h3>{resource.name}</h3>
            <p>{resource.description}</p>
            <a href={resource.url} target="_blank" rel="noreferrer">
              Visit official website
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}