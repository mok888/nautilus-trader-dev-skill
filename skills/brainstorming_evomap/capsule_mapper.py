# Copyright (C) 2025 Nautech Systems, Inc. All rights reserved.
# Nautech Systems, Inc. Proprietary and Confidential.
# Use subject to license terms.

"""Capsule mapper for converting brainstorming artifacts to EvoMap assets."""

import hashlib
import json
from typing import Any

try:
    from .envelope import compute_content_hash, generate_message_id
except ImportError:
    from envelope import compute_content_hash, generate_message_id


def map_section_delta(
    session_id: str,
    section_id: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a brainstorming section delta to an EvoMap capsule bundle.

    Parameters
    ----------
    session_id : str
        Brainstorming session identifier
    section_id : str
        Section identifier (e.g., 'architecture', 'components')
    content : str
        Section content text
    metadata : dict[str, Any], optional
        Additional metadata (approaches, constraints, decisions)

    Returns
    -------
    dict[str, Any]
        Bundle with assets (Gene, Capsule, EvolutionEvent)
    """
    if metadata is None:
        metadata = {}

    # Create Gene asset (represents the core idea/concept)
    gene_id = f"gene_{session_id}_{section_id}"
    gene = {
        "id": gene_id,
        "type": "gene",
        "content_hash": compute_content_hash(
            {"content": content, "metadata": metadata}
        ),
        "data": {
            "section": section_id,
            "content_preview": content[:500] if len(content) > 500 else content,
            "metadata": metadata,
        },
    }

    # Create Capsule asset (container for related genes)
    capsule_id = f"capsule_{session_id}_{section_id}"
    capsule = {
        "id": capsule_id,
        "type": "capsule",
        "content_hash": compute_content_hash(
            {"genes": [gene_id], "session": session_id}
        ),
        "data": {
            "session_id": session_id,
            "section_id": section_id,
            "gene_refs": [gene_id],
        },
    }

    # Create EvolutionEvent asset (tracks the evolution)
    event_id = f"event_{session_id}_{section_id}"
    evolution_event = {
        "id": event_id,
        "type": "evolution_event",
        "content_hash": compute_content_hash(
            {"capsule": capsule_id, "action": "section_delta"}
        ),
        "data": {
            "capsule_ref": capsule_id,
            "action": "section_delta",
            "session_id": session_id,
        },
    }

    return {
        "assets": [gene, capsule, evolution_event],
        "metadata": {
            "session_id": session_id,
            "section_id": section_id,
            "bundle_type": "brainstorming_delta",
        },
    }


def map_design_doc(
    session_id: str,
    design_doc_path: str,
    content: str,
    decisions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Map a finalized design document to an EvoMap capsule bundle.

    Parameters
    ----------
    session_id : str
        Brainstorming session identifier
    design_doc_path : str
        Path to the design document
    content : str
        Full design document content
    decisions : list[dict[str, Any]], optional
        List of decisions made during brainstorming

    Returns
    -------
    dict[str, Any]
        Bundle with assets representing the finalized design
    """
    if decisions is None:
        decisions = []

    # Create Gene for the full design
    gene_id = f"gene_{session_id}_design_final"
    gene = {
        "id": gene_id,
        "type": "gene",
        "content_hash": compute_content_hash({"content": content}),
        "data": {
            "type": "design_document",
            "path": design_doc_path,
            "content_preview": content[:1000] if len(content) > 1000 else content,
        },
    }

    # Create Capsule for the complete design
    capsule_id = f"capsule_{session_id}_design_final"
    capsule = {
        "id": capsule_id,
        "type": "capsule",
        "content_hash": compute_content_hash(
            {"genes": [gene_id], "decisions": decisions}
        ),
        "data": {
            "session_id": session_id,
            "type": "final_design",
            "gene_refs": [gene_id],
            "decision_count": len(decisions),
        },
    }

    # Create EvolutionEvent for the design finalization
    event_id = f"event_{session_id}_design_final"
    evolution_event = {
        "id": event_id,
        "type": "evolution_event",
        "content_hash": compute_content_hash(
            {"capsule": capsule_id, "action": "design_finalized"}
        ),
        "data": {
            "capsule_ref": capsule_id,
            "action": "design_finalized",
            "session_id": session_id,
            "decisions": decisions,
        },
    }

    return {
        "assets": [gene, capsule, evolution_event],
        "metadata": {
            "session_id": session_id,
            "bundle_type": "final_design",
            "doc_path": design_doc_path,
        },
    }


def map_decision_report(
    session_id: str,
    accepted: list[str],
    rejected: list[str],
    refined: list[str],
) -> dict[str, Any]:
    """Map a decision report to EvoMap format.

    Parameters
    ----------
    session_id : str
        Brainstorming session identifier
    accepted : list[str]
        IDs of accepted suggestions
    rejected : list[str]
        IDs of rejected suggestions
    refined : list[str]
        IDs of refined/modified suggestions

    Returns
    -------
    dict[str, Any]
        Decision report payload for EvoMap
    """
    return {
        "session_id": session_id,
        "decisions": {
            "accepted": accepted,
            "rejected": rejected,
            "refined": refined,
        },
        "counts": {
            "accepted": len(accepted),
            "rejected": len(rejected),
            "refined": len(refined),
        },
    }
