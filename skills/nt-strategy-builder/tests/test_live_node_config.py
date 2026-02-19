"""
Strategy Builder Tests: Live Node Config

Verifies that TradingNodeConfig and LiveExecEngineConfig patterns from
templates parse and build correctly. No network connections are made.
"""

import pytest

from nautilus_trader.config import (
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    LiveRiskEngineConfig,
    LoggingConfig,
    TradingNodeConfig,
)
from nautilus_trader.model.identifiers import TraderId


class TestTradingNodeConfig:
    """Verify TradingNode configuration builds from template patterns."""

    def test_basic_config_builds(self):
        """Minimal TradingNodeConfig builds without error."""
        config = TradingNodeConfig(
            trader_id=TraderId("TRADER-001"),
        )
        assert config is not None
        assert config.trader_id == TraderId("TRADER-001")

    def test_full_config_with_timeouts_builds(self):
        """Full config with all recommended timeouts builds correctly."""
        config = TradingNodeConfig(
            trader_id=TraderId("TRADER-001"),
            timeout_connection=30.0,
            timeout_reconciliation=10.0,
            timeout_portfolio=10.0,
            timeout_disconnection=10.0,
        )
        assert config.timeout_connection == 30.0
        assert config.timeout_reconciliation == 10.0

    def test_config_with_logging(self):
        """LoggingConfig attaches to TradingNodeConfig."""
        config = TradingNodeConfig(
            trader_id=TraderId("TRADER-001"),
            logging=LoggingConfig(
                log_level="INFO",
                log_directory="logs",
            ),
        )
        assert config.logging.log_level == "INFO"


class TestLiveExecEngineConfig:
    """Verify exec engine config follows recommended patterns."""

    def test_reconciliation_enabled_by_default(self):
        """Default config has reconciliation enabled."""
        config = LiveExecEngineConfig()
        assert config.reconciliation is True

    def test_recommended_lookback_mins(self):
        """open_check_lookback_mins can be set to recommended 60."""
        config = LiveExecEngineConfig(
            reconciliation=True,
            open_check_lookback_mins=60,
            inflight_check_interval_ms=2000,
            reconciliation_startup_delay_secs=10.0,
        )
        assert config.open_check_lookback_mins == 60
        assert config.reconciliation is True

    def test_lookback_below_60_is_allowed_but_warns(self):
        """
        Setting lookback_mins < 60 is technically valid but flagged by
        nt-review/SKILL.md as a red flag (causes false 'missing order' resolutions).
        This test documents that the config itself will accept it — the human
        reviewer/compliance test must catch this misuse.
        """
        config = LiveExecEngineConfig(open_check_lookback_mins=10)
        # Config accepts it (no exception) — the DO/DON'T rules warn against this
        assert config.open_check_lookback_mins == 10

    def test_full_exec_engine_config(self):
        """Full recommended config builds without error."""
        config = LiveExecEngineConfig(
            reconciliation=True,
            inflight_check_interval_ms=2000,
            open_check_interval_secs=10.0,
            open_check_lookback_mins=60,
            reconciliation_startup_delay_secs=10.0,
        )
        assert config is not None


class TestLiveRiskEngineConfig:
    """Verify risk engine config patterns."""

    def test_bypass_false_by_default(self):
        """Risk bypass should be off for production."""
        config = LiveRiskEngineConfig()
        assert config.bypass is False

    def test_order_rate_limits(self):
        """Rate limits parse from string notation."""
        config = LiveRiskEngineConfig(
            max_order_submit_rate="100/00:00:01",
            max_order_modify_rate="100/00:00:01",
        )
        assert config.max_order_submit_rate == "100/00:00:01"
