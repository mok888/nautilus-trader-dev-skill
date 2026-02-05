# Visualization in NautilusTrader

NautilusTrader v1.221.0+ introduces advanced visualization capabilities using Plotly for interactive, browser-based tearsheets.

## Requirements

Ensure you have Plotly installed in your environment:

```bash
uv add plotly
# or
pip install "plotly>=6.3.1"
```

## Features

- **Interactive Tearsheets**: Zoom, hover, and filter charts in a self-contained HTML file.
- **Dark Mode Support**: Native dark and light themes for all charts.
- **Chart Registry**: Extensible system to add your own custom Plotly charts.
- **Plugin System**: Decoupled visualization architecture.

## Primary Metrics

The new tearsheets include critical performance metrics by default:
- **CAGR**: Compound Annual Growth Rate.
- **Calmar Ratio**: Annualized return relative to maximum drawdown.
- **Max Drawdown**: The largest peak-to-trough decline.

## Usage Example

```python
from nautilus_trader.analysis.visualizer import BacktestVisualizer

visualizer = BacktestVisualizer(results=results)
visualizer.tearsheet(output_path="report.html")
```

See [backtest_viz.py](../skills/nt-implement/templates/backtest_viz.py) for a full template.
