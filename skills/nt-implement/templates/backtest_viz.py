from nautilus_trader.analysis.visualizer import BacktestVisualizer
from nautilus_trader.analysis.statistics import PortfolioAnalyzer
from nautilus_trader.backtest.engine import BacktestEngine

# 1. Run your backtest
engine = BacktestEngine()
# ... engine setup and run ...

# 2. Get results
results = engine.get_results()

# 3. Initialize Visualizer (requires plotly>=6.3.1)
visualizer = BacktestVisualizer(
    results=results,
    theme="dark",  # "light" or "dark"
)

# 4. Generate comprehensive tearsheet
visualizer.tearsheet(
    output_path="backtest_report.html",
    include_plots=[
        "equity_curve",
        "drawdowns",
        "monthly_returns",
        "position_history",
        "trade_distribution",
    ],
    # Add new v1.221.0 statistics
    statistics=["CAGR", "Calmar Ratio", "Max Drawdown"],
)

# 5. Create custom plot
fig = visualizer.plot_equity_curve()
fig.update_layout(title="Customized Equity Curve")
fig.show()
