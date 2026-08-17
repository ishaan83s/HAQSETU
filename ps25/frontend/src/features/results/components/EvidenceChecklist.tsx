type EvidenceChecklistProps = {
  items: string[]
}

export default function EvidenceChecklist({
  items,
}: EvidenceChecklistProps) {
  return (
    <section>
      <h2>Evidence to keep safe</h2>

      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}