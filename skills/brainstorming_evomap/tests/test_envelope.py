# Copyright (C) 2025 Nautech Systems, Inc. All rights reserved.
# Nautech Systems, Inc. Proprietary and Confidential.
# Use subject to license terms.

"""Tests for A2A envelope builder and validation."""

import importlib.util
from pathlib import Path

import pytest

_module_dir = Path(__file__).parent.parent


def _load_module(name: str):
    """Load a module directly from file path."""
    path = _module_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


envelope = _load_module("envelope")


def test_envelope_contains_required_fields():
    """Envelope must contain all required A2A fields."""
    msg = envelope.build_envelope(
        message_type="publish",
        sender_id="node_test123",
        payload={"k": "v"},
    )

    for key in [
        "protocol",
        "protocol_version",
        "message_type",
        "message_id",
        "sender_id",
        "timestamp",
        "payload",
    ]:
        assert key in msg, f"Missing required field: {key}"


def test_envelope_uses_correct_protocol():
    """Envelope must use gep-a2a protocol v1.0.0."""
    msg = envelope.build_envelope(
        message_type="publish",
        sender_id="node_test",
        payload={},
    )

    assert msg["protocol"] == "gep-a2a"
    assert msg["protocol_version"] == "1.0.0"


def test_message_id_is_unique():
    """Generated message IDs should be unique."""
    ids = [envelope.generate_message_id() for _ in range(10)]
    assert len(set(ids)) == 10


def test_node_id_format():
    """Node IDs should have correct prefix."""
    node_id = envelope.generate_node_id()
    assert node_id.startswith("node_")


def test_content_hash_is_deterministic():
    """Same content should produce same hash."""
    data = {"test": "value", "nested": {"a": 1}}
    hash1 = envelope.compute_content_hash(data)
    hash2 = envelope.compute_content_hash(data)
    assert hash1 == hash2


def test_content_hash_differs_for_different_content():
    """Different content should produce different hashes."""
    hash1 = envelope.compute_content_hash({"a": 1})
    hash2 = envelope.compute_content_hash({"a": 2})
    assert hash1 != hash2


def test_validate_envelope_accepts_valid():
    """Valid envelope should pass validation."""
    msg = envelope.build_envelope(
        message_type="publish",
        sender_id="node_test",
        payload={},
    )
    is_valid, errors = envelope.validate_envelope(msg)
    assert is_valid
    assert errors == []


def test_validate_envelope_rejects_missing_fields():
    """Envelope missing fields should fail validation."""
    is_valid, errors = envelope.validate_envelope({"protocol": "gep-a2a"})
    assert not is_valid
    assert any("Missing required field" in e for e in errors)


def test_validate_envelope_rejects_wrong_protocol():
    """Envelope with wrong protocol should fail validation."""
    msg = envelope.build_envelope(
        message_type="publish",
        sender_id="node_test",
        payload={},
    )
    msg["protocol"] = "wrong-protocol"
    is_valid, errors = envelope.validate_envelope(msg)
    assert not is_valid
    assert any("Invalid protocol" in e for e in errors)
