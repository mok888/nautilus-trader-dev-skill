"""
DEX Adapter Tests: Structural Compliance

Verifies that the DEX adapter template classes expose ALL methods required
by the NautilusTrader adapter framework. This test suite acts as a gate
before acceptance testing on a live or forked network.

These checks mirror the compliance_checklist.md items that can be
automatically validated.

NOTE: These tests check method PRESENCE only. Functional correctness is
tested in `test_instrument_parsing.py` and `test_order_book_events.py`.
"""

import sys
import importlib.util
from inspect import iscoroutinefunction
from pathlib import Path

import pytest

_templates = Path(__file__).parent.parent / "templates"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, _templates / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Load all template modules
_config_mod = _load_module("dex_config")
_provider_mod = _load_module("dex_instrument_provider")
_data_mod = _load_module("dex_data_client")
_exec_mod = _load_module("dex_exec_client")
_factory_mod = _load_module("dex_factory")

MyDEXInstrumentProviderConfig = _config_mod.MyDEXInstrumentProviderConfig
MyDEXDataClientConfig = _config_mod.MyDEXDataClientConfig
MyDEXExecClientConfig = _config_mod.MyDEXExecClientConfig
MyDEXInstrumentProvider = _provider_mod.MyDEXInstrumentProvider
MyDEXDataClient = _data_mod.MyDEXDataClient
MyDEXExecutionClient = _exec_mod.MyDEXExecutionClient
MyDEXLiveDataClientFactory = _factory_mod.MyDEXLiveDataClientFactory
MyDEXLiveExecClientFactory = _factory_mod.MyDEXLiveExecClientFactory


class TestInstrumentProviderInterface:
    """Checks all required InstrumentProvider methods are present and async."""

    def test_load_all_async_exists(self):
        assert hasattr(MyDEXInstrumentProvider, "load_all_async")

    def test_load_all_async_is_coroutine(self):
        assert iscoroutinefunction(MyDEXInstrumentProvider.load_all_async)

    def test_load_ids_async_exists(self):
        assert hasattr(MyDEXInstrumentProvider, "load_ids_async")

    def test_load_ids_async_is_coroutine(self):
        assert iscoroutinefunction(MyDEXInstrumentProvider.load_ids_async)

    def test_get_all_exists(self):
        assert hasattr(MyDEXInstrumentProvider, "get_all")

    def test_find_exists(self):
        assert hasattr(MyDEXInstrumentProvider, "find")

    def test_parse_pool_to_instrument_exists(self):
        assert hasattr(MyDEXInstrumentProvider, "_parse_pool_to_instrument")


class TestDataClientInterface:
    """Checks all required LiveMarketDataClient methods are present."""

    REQUIRED_ASYNC_METHODS = [
        "_connect",
        "_disconnect",
        "_subscribe_quote_ticks",
        "_subscribe_trade_ticks",
        "_subscribe_order_book_deltas",
        "_unsubscribe_quote_ticks",
        "_unsubscribe_trade_ticks",
        "_unsubscribe_order_book_deltas",
        "_request_bars",
    ]

    @pytest.mark.parametrize("method", REQUIRED_ASYNC_METHODS)
    def test_method_exists_and_is_async(self, method):
        assert hasattr(MyDEXDataClient, method), f"Missing: {method}"
        assert iscoroutinefunction(getattr(MyDEXDataClient, method)), (
            f"Not async: {method}"
        )

    def test_reserves_to_quote_tick_exists(self):
        assert hasattr(MyDEXDataClient, "_reserves_to_quote_tick")

    def test_swap_event_to_trade_tick_exists(self):
        assert hasattr(MyDEXDataClient, "_swap_event_to_trade_tick")


class TestExecutionClientInterface:
    """Checks all required LiveExecutionClient methods are present."""

    REQUIRED_ASYNC_METHODS = [
        "_connect",
        "_disconnect",
        "_submit_order",
        "_cancel_order",
        "_cancel_all_orders",
        "_modify_order",
        "_query_order",
        "generate_order_status_report",
    ]

    @pytest.mark.parametrize("method", REQUIRED_ASYNC_METHODS)
    def test_method_exists_and_is_async(self, method):
        assert hasattr(MyDEXExecutionClient, method), f"Missing: {method}"
        assert iscoroutinefunction(getattr(MyDEXExecutionClient, method)), (
            f"Not async: {method}"
        )

    def test_update_account_state_exists(self):
        assert hasattr(MyDEXExecutionClient, "_update_account_state")
        assert iscoroutinefunction(MyDEXExecutionClient._update_account_state)

    def test_wait_for_receipt_exists(self):
        assert hasattr(MyDEXExecutionClient, "_wait_for_receipt")
        assert iscoroutinefunction(MyDEXExecutionClient._wait_for_receipt)


class TestConfigInterface:
    """Checks that all config classes have required security-sensitive fields."""

    @staticmethod
    def _has_field(config_cls, name: str) -> bool:
        model_fields = getattr(config_cls, "model_fields", None)
        if model_fields is not None:
            return name in model_fields
        legacy_fields = getattr(config_cls, "__fields__", None)
        if legacy_fields is not None:
            return name in legacy_fields
        return hasattr(config_cls, name)

    def test_exec_config_has_secret_str_private_key(self):
        """Private key must be SecretStr, not plain str."""
        from pydantic import SecretStr

        config = MyDEXExecClientConfig()
        assert hasattr(config, "private_key"), (
            "private_key field missing from ExecClientConfig"
        )
        assert isinstance(config.private_key, SecretStr), (
            f"private_key must be SecretStr, got {type(config.private_key)}. "
            "Plain str leaks keys in logs and repr()!"
        )

    def test_exec_config_has_sandbox_mode(self):
        assert self._has_field(MyDEXExecClientConfig, "sandbox_mode")

    def test_exec_config_has_max_slippage_bps(self):
        assert self._has_field(MyDEXExecClientConfig, "max_slippage_bps")

    def test_data_config_has_poll_interval(self):
        assert self._has_field(MyDEXDataClientConfig, "poll_interval_secs")

    def test_provider_config_has_sandbox_mode(self):
        assert self._has_field(MyDEXInstrumentProviderConfig, "sandbox_mode")


class TestFactoryInterface:
    """Checks that factory classes expose static create() methods."""

    def test_data_factory_has_create(self):
        assert hasattr(MyDEXLiveDataClientFactory, "create")

    def test_exec_factory_has_create(self):
        assert hasattr(MyDEXLiveExecClientFactory, "create")
