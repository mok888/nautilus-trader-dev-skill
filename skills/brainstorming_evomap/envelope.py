# Copyright (C) 2025 Nautech Systems, Inc. All rights reserved.
# Nautech Systems, Inc. Proprietary and Confidential.
# Use subject to license terms.

"""A2A envelope builder and validation for EvoMap protocol."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


PROTOCOL = "gep-a2a"
PROTOCOL_VERSION = "1.0.0"


def generate_message_id() -> str:
    """Generate a unique message ID.

    Returns
    -------
    str
        UUID-based message identifier
    """
    return f"msg_{uuid.uuid4().hex[:24]}"


def generate_node_id() -> str:
    """Generate a unique node ID.

    Returns
    -------
    str
        Node identifier prefixed with 'node_'
    """
    return f"node_{uuid.uuid4().hex[:20]}"


def compute_content_hash(data: dict[str, Any]) -> str:
    """Compute SHA256 hash of canonical JSON representation.

    Parameters
    ----------
    data : dict[str, Any]
        Data to hash

    Returns
    -------
    str
        Hex-encoded SHA256 hash
    """
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_envelope(
    message_type: str,
    sender_id: str,
    payload: dict[str, Any],
    message_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a valid A2A protocol envelope.

    Parameters
    ----------
    message_type : str
        Type of message (e.g., 'publish', 'fetch', 'report')
    sender_id : str
        Node identifier of the sender
    payload : dict[str, Any]
        Message payload
    message_id : str, optional
        Unique message ID (generated if not provided)
    timestamp : str, optional
        ISO 8601 timestamp (generated if not provided)

    Returns
    -------
    dict[str, Any]
        Complete A2A envelope with all required fields
    """
    if message_id is None:
        message_id = generate_message_id()
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "protocol": PROTOCOL,
        "protocol_version": PROTOCOL_VERSION,
        "message_type": message_type,
        "message_id": message_id,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "payload": payload,
    }


def validate_envelope(envelope: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate an A2A envelope has all required fields.

    Parameters
    ----------
    envelope : dict[str, Any]
        Envelope to validate

    Returns
    -------
    tuple[bool, list[str]]
        (is_valid, list of errors)
    """
    required_fields = [
        "protocol",
        "protocol_version",
        "message_type",
        "message_id",
        "sender_id",
        "timestamp",
        "payload",
    ]

    errors = []

    for field in required_fields:
        if field not in envelope:
            errors.append(f"Missing required field: {field}")

    if "protocol" in envelope and envelope["protocol"] != PROTOCOL:
        errors.append(
            f"Invalid protocol: expected {PROTOCOL}, got {envelope['protocol']}"
        )

    if (
        "protocol_version" in envelope
        and envelope["protocol_version"] != PROTOCOL_VERSION
    ):
        errors.append(
            f"Invalid protocol_version: expected {PROTOCOL_VERSION}, got {envelope['protocol_version']}"
        )

    return len(errors) == 0, errors
