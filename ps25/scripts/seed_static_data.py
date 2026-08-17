"""Manually seed the curated legal-aid contact data after deployment.

This script is intentionally not called by application startup. Run it manually
from the ``ps25`` directory after the database schema has been created.
"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from common.db import sync_session_factory  # noqa: E402
from common.models import LegalAidContact  # noqa: E402


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


if __name__ == "__main__":
    seed_legal_aid_contacts()
