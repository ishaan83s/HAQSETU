import type { GetIncidentResponse } from "@/lib/incidents"
import type { LegalAwarenessResult } from "./types"

export function adaptIncidentResult(
  response: GetIncidentResponse,
): LegalAwarenessResult {
  const { triage } = response

  const urgencyMap: Record<
    GetIncidentResponse["triage"]["urgency"],
    LegalAwarenessResult["urgency"]
  > = {
    general: "low",
    time_sensitive: "medium",
    urgent: "high",
  }

  const urgency = urgencyMap[triage.urgency]

  const nextSteps = triage.cards.whatYouCanDoNext.map((claim, index) => ({
    title: `Next step ${index + 1}`,
    description: claim.text,
  }))

  const officialResources = triage.cards.whatMayProtectYou.map(
    (claim) => ({
      name: claim.source.title,
      description: claim.text,
      url: claim.source.sourceUrl,
      section: claim.source.section,
      jurisdictionState: claim.source.jurisdictionState,
      effectiveDate: claim.source.effectiveDate,
      versionLabel: claim.source.versionLabel,
    }),
  )

  return {
    incidentSummary: triage.cards.whatMayBeHappening.text,
    possibleIssue:
      triage.issues.map((issue) => issue.type).join(", ") ||
      "No specific issue identified.",
    urgency,
    urgencyMessage:
      triage.urgency === "urgent"
        ? "This situation may require prompt attention."
        : triage.urgency === "time_sensitive"
          ? "This situation may involve a time-sensitive step."
          : "This situation does not currently indicate an urgent response.",
    evidenceChecklist: triage.cards.evidenceToKeep,
    nextSteps,
    officialResources,
    legalAid: {
      name: triage.cards.legalAid.name,
      contactInfo: triage.cards.legalAid.contactInfo,
    },
    disclaimer:
      "HAQSETU provides legal awareness and navigation support. It does not provide legal advice or representation.",
  }
}
