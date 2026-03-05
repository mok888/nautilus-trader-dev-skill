# Copyright (C) 2025 Nautech Systems, Inc. All rights reserved.
# Nautech Systems, Inc. Proprietary and Confidential.
# Use subject to license terms.

"""Contract tests for EvoMap Capsule Client."""

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


_client_mod = _load_module("evomap_capsule_client")
EvoMapCapsuleClient = _client_mod.EvoMapCapsuleClient


def test_client_exposes_required_methods():
    """Client must expose the core A2A endpoint methods."""
    client = EvoMapCapsuleClient(base_url="https://evomap.ai", api_key="test-key")

    for name in ["hello", "publish", "fetch", "report"]:
        assert hasattr(client, name), f"Client missing required method: {name}"


def test_client_hello_returns_ok():
    """Hello endpoint should return a valid response structure."""
    client = EvoMapCapsuleClient(base_url="https://mock", api_key="test-key")
    response = client.hello()

    assert isinstance(response, dict)
    assert "ok" in response
