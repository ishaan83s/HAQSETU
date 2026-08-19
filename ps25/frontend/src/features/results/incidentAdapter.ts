import type { GetIncidentResponse } from "@/lib/incidents"
import type { LegalAwarenessResult, OfficialResource } from "./types"

export function adaptIncidentResult(
  response: GetIncidentResponse,
): LegalAwarenessResult {
  const { triage } = response

  const possibleIssues = (triage.issues || [])
    .map((issue) => issue.type)
    .filter(Boolean)

  const whatMayProtectYou = (triage.cards?.whatMayProtectYou || []).map((claim) => ({
    text: claim.text,
    source: claim.source || null,
  }))

  const nextSteps = (triage.cards?.whatYouCanDoNext || []).map((claim, index) => ({
    title: `Step ${index + 1}`,
    description: claim.text,
    source: claim.source || null,
  }))

  // Collect unique official resources from both whatMayProtectYou and whatYouCanDoNext
  const resourceMap = new Map<string, OfficialResource>()

  for (const claim of triage.cards?.whatMayProtectYou || []) {
    if (claim.source && claim.source.title) {
      const key = `${claim.source.title}-${claim.source.section || ""}`
      if (!resourceMap.has(key)) {
        resourceMap.set(key, {
          name: claim.source.title,
          description: claim.text,
          section: claim.source.section || null,
          url: claim.source.sourceUrl,
          jurisdictionState: claim.source.jurisdictionState || null,
          effectiveDate: claim.source.effectiveDate || null,
          versionLabel: claim.source.versionLabel || null,
        })
      }
    }
  }

  for (const step of triage.cards?.whatYouCanDoNext || []) {
    if (step.source && step.source.title) {
      const key = `${step.source.title}-${step.source.section || ""}`
      if (!resourceMap.has(key)) {
        resourceMap.set(key, {
          name: step.source.title,
          description: step.text,
          section: step.source.section || null,
          url: step.source.sourceUrl,
          jurisdictionState: step.source.jurisdictionState || null,
          effectiveDate: step.source.effectiveDate || null,
          versionLabel: step.source.versionLabel || null,
        })
      }
    }
  }

  const officialResources = Array.from(resourceMap.values())

  const legalAid =
    triage.cards?.legalAid &&
    (triage.cards.legalAid.name || triage.cards.legalAid.contactInfo)
      ? {
          name: triage.cards.legalAid.name,
          contactInfo: triage.cards.legalAid.contactInfo,
        }
      : null

  const urgencyMessage =
    triage.urgency === "urgent"
      ? "This situation may require prompt attention."
      : triage.urgency === "time_sensitive"
        ? "This situation involves time-sensitive steps."
        : "Standard legal awareness guidance."

  return {
    incidentSummary: triage.cards?.whatMayBeHappening?.text || "",
    possibleIssues,
    actor: triage.actor || null,
    jurisdictionState: triage.jurisdictionState || null,
    urgency: triage.urgency,
    urgencyMessage,
    whatMayProtectYou,
    evidenceChecklist: triage.cards?.evidenceToKeep || [],
    nextSteps,
    officialResources,
    legalAid,
    disclaimer:
      "HAQSETU provides general legal awareness and information to help citizens understand their rights. It does not provide personalized legal representation or legal advice.",
  }
}
