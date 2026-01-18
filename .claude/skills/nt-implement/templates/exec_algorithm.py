"""
Execution Algorithm Template for nautilus_trader.

Execution algorithms manage how orders are executed, potentially splitting
large orders into smaller child orders over time.
"""

from decimal import Decimal

import pandas as pd

from nautilus_trader.config import ExecAlgorithmConfig
from nautilus_trader.execution.algorithm import ExecAlgorithm
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import OrderSide
from nautilus_trader.model import Quantity
from nautilus_trader.model import TimeInForce
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import Order


class MyExecAlgorithmConfig(ExecAlgorithmConfig):
    """
    Configuration for MyExecAlgorithm.

    Parameters
    ----------
    exec_algorithm_id : str
        Unique identifier for this algorithm (default: class name).
    """

    # No additional config needed for this example
    pass


class MyExecAlgorithm(ExecAlgorithm):
    """
    Example execution algorithm.

    Splits a primary order into smaller child orders executed over time.
    Similar to TWAP (Time-Weighted Average Price).

    Parameters
    ----------
    config : MyExecAlgorithmConfig
        The algorithm configuration.
    """

    def __init__(self, config: MyExecAlgorithmConfig | None = None) -> None:
        """
        Initialize the execution algorithm.

        Parameters
        ----------
        config : MyExecAlgorithmConfig, optional
            The algorithm configuration.
        """
        super().__init__(config or MyExecAlgorithmConfig())

        # Track active orders
        self._scheduled_sizes: dict[str, list[Quantity]] = {}

    def on_start(self) -> None:
        """Handle algorithm start."""
        self.log.info("Execution algorithm started")

    def on_stop(self) -> None:
        """Handle algorithm stop."""
        self._scheduled_sizes.clear()

    def on_order(self, order: Order) -> None:
        """
        Handle incoming order to be executed by this algorithm.

        Parameters
        ----------
        order : Order
            The primary order to execute.
        """
        # Get execution parameters from order
        params = order.exec_algorithm_params or {}
        horizon_secs = params.get("horizon_secs", 60)
        interval_secs = params.get("interval_secs", 10)

        if interval_secs <= 0 or horizon_secs <= 0:
            self.log.error("Invalid horizon or interval")
            return

        # Calculate number of slices
        num_slices = max(1, int(horizon_secs / interval_secs))

        # Get instrument for quantity precision
        instrument: Instrument | None = self.cache.instrument(order.instrument_id)
        if instrument is None:
            self.log.error(f"Instrument not found: {order.instrument_id}")
            return

        # Split quantity into slices
        total_qty = float(order.quantity)
        slice_qty = total_qty / num_slices
        sizes = self._calculate_slice_sizes(instrument, total_qty, num_slices)

        # Store scheduled sizes
        order_key = order.client_order_id.value
        self._scheduled_sizes[order_key] = sizes

        # Submit first child immediately
        self._submit_child(order, sizes[0], 0, num_slices)

        # Schedule remaining slices
        for i in range(1, num_slices):
            self.clock.set_time_alert(
                name=f"{order_key}_slice_{i}",
                alert_time=self.clock.utc_now() + pd.Timedelta(seconds=interval_secs * i),
                callback=lambda event, idx=i: self._on_scheduled_slice(order, idx, num_slices),
            )

    def on_order_filled(self, event: OrderFilled) -> None:
        """
        Handle child order fill event.

        Parameters
        ----------
        event : OrderFilled
            The fill event.
        """
        self.log.debug(f"Child order filled: {event.last_qty} @ {event.last_px}")

    def _calculate_slice_sizes(
        self,
        instrument: Instrument,
        total_qty: float,
        num_slices: int,
    ) -> list[Quantity]:
        """
        Calculate slice sizes for order splitting.

        Parameters
        ----------
        instrument : Instrument
            The instrument (for quantity precision).
        total_qty : float
            Total quantity to split.
        num_slices : int
            Number of slices.

        Returns
        -------
        list[Quantity]
            List of quantities for each slice.
        """
        base_size = total_qty / num_slices
        sizes: list[Quantity] = []
        remaining = total_qty

        for i in range(num_slices - 1):
            size = instrument.make_qty(Decimal(str(base_size)))
            sizes.append(size)
            remaining -= float(size)

        # Last slice gets remainder
        sizes.append(instrument.make_qty(Decimal(str(remaining))))

        return sizes

    def _submit_child(
        self,
        parent: Order,
        quantity: Quantity,
        slice_idx: int,
        total_slices: int,
    ) -> None:
        """
        Submit a child order.

        Parameters
        ----------
        parent : Order
            The parent order.
        quantity : Quantity
            Quantity for this child.
        slice_idx : int
            Index of this slice.
        total_slices : int
            Total number of slices.
        """
        # For the last slice, submit the original parent order
        if slice_idx == total_slices - 1:
            self.submit_order(parent)
            return

        # Create and submit child order
        child = self.spawn_market(
            primary=parent,
            quantity=quantity,
            time_in_force=TimeInForce.IOC,
        )
        self.submit_order(child)

    def _on_scheduled_slice(
        self,
        parent: Order,
        slice_idx: int,
        total_slices: int,
    ) -> None:
        """
        Handle scheduled slice execution.

        Parameters
        ----------
        parent : Order
            The parent order.
        slice_idx : int
            Index of this slice.
        total_slices : int
            Total number of slices.
        """
        order_key = parent.client_order_id.value
        sizes = self._scheduled_sizes.get(order_key)

        if sizes is None or slice_idx >= len(sizes):
            return

        self._submit_child(parent, sizes[slice_idx], slice_idx, total_slices)


# =============================================================================
# Usage in Strategy
# =============================================================================
#
# # In strategy configuration or engine setup:
# exec_algorithm = MyExecAlgorithm()
# engine.add_exec_algorithm(exec_algorithm)
#
# # In strategy order submission:
# order = self.order_factory.market(
#     instrument_id=self.instrument_id,
#     order_side=OrderSide.BUY,
#     quantity=self.instrument.make_qty(1000),
#     exec_algorithm_id=ExecAlgorithmId("MyExecAlgorithm"),
#     exec_algorithm_params={"horizon_secs": 60, "interval_secs": 10},
# )
# self.submit_order(order)
