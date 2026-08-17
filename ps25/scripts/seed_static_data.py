"""Manually seed the curated legal-aid, evidence checklist, and legal source data after deployment.

This script is intentionally not called by application startup. Run it manually
from the ``ps25`` directory after the database schema has been created.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import select


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from common.db import sync_session_factory  # noqa: E402
from common.models import EvidenceChecklist, LegalAidContact, LegalSource  # noqa: E402

CORPUS_DOCS_DIR = Path(__file__).resolve().parents[1] / "backend" / "triage" / "corpus" / "documents"


LEGAL_AID_CONTACTS = (
    {
        "state": "Maharashtra",
        "name": "Maharashtra State Legal Services Authority (MSLSA)",
        "contact_info": "Helpline: 1800-22-2324 / Phone: 022-22691395",
        "display_order": 1,
    },
    {
        "state": "Maharashtra",
        "name": "High Court Legal Services Committee, Mumbai",
        "contact_info": "Phone: 8591903603 / Email: hclsc-mum.mh@bhc.gov.in",
        "display_order": 2,
    },
    {
        "state": "central",
        "name": "National Legal Services Authority (NALSA)",
        "contact_info": "National Toll-Free Helpline: 15100",
        "display_order": 1,
    },
)

EVIDENCE_CHECKLISTS = (
    {
        "incident_type": "wage_nonpayment",
        "items": [
            "salary slips",
            "bank statements",
            "written communication",
        ],
    },
    {
        "incident_type": "wrongful_termination",
        "items": [
            "termination message or letter",
            "employment records",
            "written communication",
        ],
    },
    {
        "incident_type": "tenancy_eviction",
        "items": [
            "rent agreement",
            "rent or payment records",
            "eviction/lockout communication",
        ],
    },
    {
        "incident_type": "unsupported",
        "items": [
            "any written communication",
            "payment records",
            "dated photos",
        ],
    },
)


def seed_legal_aid_contacts() -> None:
    """Insert or synchronize the canonical legal-aid contacts idempotently."""
    with sync_session_factory() as session:
        for contact_data in LEGAL_AID_CONTACTS:
            contact = session.scalar(
                select(LegalAidContact).where(
                    LegalAidContact.state == contact_data["state"],
                    LegalAidContact.name == contact_data["name"],
                )
            )

            if contact is None:
                session.add(LegalAidContact(**contact_data))
            else:
                contact.contact_info = contact_data["contact_info"]
                contact.display_order = contact_data["display_order"]

        session.commit()


def seed_evidence_checklists() -> None:
    """Insert or synchronize the canonical evidence checklists idempotently."""
    with sync_session_factory() as session:
        for checklist_data in EVIDENCE_CHECKLISTS:
            checklist = session.scalar(
                select(EvidenceChecklist).where(
                    EvidenceChecklist.incident_type == checklist_data["incident_type"],
                )
            )

            if checklist is None:
                session.add(EvidenceChecklist(**checklist_data))
            else:
                checklist.items = checklist_data["items"]

        session.commit()


def seed_legal_sources() -> None:
    """Insert or verify the canonical legal sources from corpus documents idempotently."""
    json_paths = sorted(CORPUS_DOCS_DIR.glob("*.json"))
    if not json_paths:
        raise RuntimeError(f"No corpus documents found in {CORPUS_DOCS_DIR}")

    with sync_session_factory() as session:
        for json_path in json_paths:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            source_id = uuid.UUID(data["sourceId"])
            eff_date = date.fromisoformat(data["effectiveDate"]) if data.get("effectiveDate") else None

            existing = session.scalar(
                select(LegalSource).where(LegalSource.id == source_id)
            )

            if existing is None:
                new_source = LegalSource(
                    id=source_id,
                    title=data["title"],
                    section=data.get("section"),
                    domain=data["domain"],
                    jurisdiction_state=data["jurisdictionState"],
                    source_url=data["sourceUrl"],
                    effective_date=eff_date,
                    version_label=data.get("versionLabel"),
                )
                session.add(new_source)
            else:
                # Idempotency check: verify existing row matches corpus metadata exactly
                if (
                    existing.title != data["title"]
                    or existing.section != data.get("section")
                    or existing.domain != data["domain"]
                    or existing.jurisdiction_state != data["jurisdictionState"]
                    or existing.source_url != data["sourceUrl"]
                    or existing.effective_date != eff_date
                    or existing.version_label != data.get("versionLabel")
                ):
                    raise RuntimeError(
                        f"Conflicting metadata for existing LegalSource {source_id} in {json_path.name}"
                    )

        session.commit()


if __name__ == "__main__":
    seed_legal_aid_contacts()
    seed_evidence_checklists()
    seed_legal_sources()
