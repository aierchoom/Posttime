"""
经典“全天候”零售代理与 Harry Browne 永久组合的可复现 ETF 回测。

数据：Yahoo Finance chart API 的 adjusted close（已在参考财报资料池归档）。
口径：USD、税前、含分红/票息复投，不含个人税费与汇率换算。
执行：信号在收盘后生成，下一交易日收盘后调仓，新权重从再下一交易日的收盘间回报开始生效。

这是研究代码，不是买卖指令。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


TOPIC = "全天候与永久投资组合策略回测"
HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
DATA_DIR = WORKSPACE / "参考财报" / "产业链研究" / TOPIC

TICKERS = ["SPY", "TLT", "IEF", "GLD", "DBC", "BIL"]
EVAL_START = pd.Timestamp("2008-07-01")
EVAL_END = pd.Timestamp("2026-07-31")
TARGET_VOL = 0.10
VOL_LOOKBACK = 60

# 单边名义交易成本：佣金 + 半个买卖价差 + 滑点的简化合计。
# ETF 净值/复权价已反映基金内部费率，不重复扣除。
BASE_COSTS = {
    "SPY": 0.0005,
    "TLT": 0.0005,
    "IEF": 0.0005,
    "GLD": 0.0005,
    "DBC": 0.0010,
    "BIL": 0.0002,
}

PORTFOLIOS = {
    # 这是 Tony Robbins 著作传播的 All Seasons 可交易代理，
    # 不是 Bridgewater 对外披露的恒定持仓。
    "AW-retail-proxy": {
        "SPY": 0.30,
        "TLT": 0.40,
        "IEF": 0.15,
        "GLD": 0.075,
        "DBC": 0.075,
        "BIL": 0.00,
    },
    "Permanent-25x4": {
        "SPY": 0.25,
        "TLT": 0.25,
        "IEF": 0.00,
        "GLD": 0.25,
        "DBC": 0.00,
        "BIL": 0.25,
    },
}

STRATEGY_LABELS = {
    "buy_hold": "买入持有漂移",
    "annual_rebalance": "年度再平衡",
    "browne_15_35": "Browne年检15/35阈值",
    "monthly_rebalance": "月度再平衡对照",
    "sma_10m": "10月均线",
    "sma_200d": "200日均线",
    "abs_mom_12m": "12月绝对动量",
    "dual_mom_top2": "12月双动量Top2",
    "vol_cap_10": "10%波动率上限",
}


@dataclass
class SimulationResult:
    daily_return: pd.Series
    equity: pd.Series
    cash_weight: pd.Series
    turnover: pd.Series
    cost_dollars: pd.Series
    trade_log: pd.DataFrame


def load_adjusted_prices() -> pd.DataFrame:
    series: dict[str, pd.Series] = {}
    for ticker in TICKERS:
        path = DATA_DIR / f"2026-08-12_YahooFinance_{ticker}_日线含复权.json"
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        result = payload["chart"]["result"][0]
        dates = pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_localize(None).normalize()
        adjusted = result["indicators"]["adjclose"][0]["adjclose"]
        s = pd.Series(adjusted, index=dates, name=ticker, dtype="float64")
        series[ticker] = s[~s.index.duplicated(keep="last")]

    prices = pd.concat(series.values(), axis=1, join="inner").sort_index()
    prices = prices.loc[:EVAL_END].dropna(how="any")
    if list(prices.columns) != TICKERS:
        raise AssertionError(f"行情列异常: {list(prices.columns)}")
    if prices.index.min() > pd.Timestamp("2007-05-30"):
        raise AssertionError("共同样本起点晚于预期")
    if prices.index.max() != EVAL_END:
        raise AssertionError(f"数据截止日异常: {prices.index.max().date()}")
    return prices


def normalized_weights(raw: dict[str, float]) -> pd.Series:
    w = pd.Series({ticker: float(raw.get(ticker, 0.0)) for ticker in TICKERS})
    if not math.isclose(float(w.sum()), 1.0, abs_tol=1e-12):
        raise AssertionError(f"权重不等于 1: {w.sum()}")
    if (w < -1e-12).any():
        raise AssertionError("主回测不允许卖空")
    return w


def next_trading_day(index: pd.DatetimeIndex, signal_date: pd.Timestamp) -> pd.Timestamp | None:
    position = int(index.searchsorted(signal_date, side="right"))
    if position >= len(index):
        return None
    return index[position]


def month_end_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.groupby(prices.index.to_period("M"), sort=True).tail(1)


def filtered_target(base: pd.Series, active: pd.Series) -> pd.Series:
    target = pd.Series(0.0, index=TICKERS)
    target["BIL"] = base["BIL"]
    for ticker in TICKERS:
        if ticker == "BIL" or base[ticker] == 0:
            continue
        if bool(active.get(ticker, False)):
            target[ticker] += base[ticker]
        else:
            target["BIL"] += base[ticker]
    if not math.isclose(float(target.sum()), 1.0, abs_tol=1e-10):
        raise AssertionError(f"过滤后权重不等于 1: {target.sum()}")
    return target


def schedule_monthly_constant(prices: pd.DataFrame, base: pd.Series) -> dict[pd.Timestamp, pd.Series]:
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in month_end_prices(prices).index:
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = base.copy()
    return schedule


def schedule_annual(prices: pd.DataFrame, base: pd.Series) -> dict[pd.Timestamp, pd.Series]:
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in month_end_prices(prices).index:
        if signal_date.month != 12:
            continue
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = base.copy()
    return schedule


def schedule_sma_monthly(
    prices: pd.DataFrame, base: pd.Series, window: int
) -> dict[pd.Timestamp, pd.Series]:
    monthly = month_end_prices(prices)
    moving_average = monthly.rolling(window=window, min_periods=window).mean()
    risky = [ticker for ticker in TICKERS if ticker != "BIL" and base[ticker] > 0]
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in monthly.index:
        if moving_average.loc[signal_date, risky].isna().any():
            continue
        active = monthly.loc[signal_date, risky] > moving_average.loc[signal_date, risky]
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = filtered_target(base, active)
    return schedule


def schedule_sma_daily(
    prices: pd.DataFrame, base: pd.Series, window: int
) -> dict[pd.Timestamp, pd.Series]:
    moving_average = prices.rolling(window=window, min_periods=window).mean()
    risky = [ticker for ticker in TICKERS if ticker != "BIL" and base[ticker] > 0]
    prior_state: tuple[bool, ...] | None = None
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in prices.index:
        if moving_average.loc[signal_date, risky].isna().any():
            continue
        state = tuple(
            bool(prices.loc[signal_date, ticker] > moving_average.loc[signal_date, ticker])
            for ticker in risky
        )
        if state == prior_state:
            continue
        prior_state = state
        active = pd.Series(state, index=risky)
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = filtered_target(base, active)
    return schedule


def schedule_absolute_momentum(
    prices: pd.DataFrame, base: pd.Series, months: int
) -> dict[pd.Timestamp, pd.Series]:
    monthly = month_end_prices(prices)
    momentum = monthly / monthly.shift(months) - 1.0
    risky = [ticker for ticker in TICKERS if ticker != "BIL" and base[ticker] > 0]
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in monthly.index:
        values = momentum.loc[signal_date, risky + ["BIL"]]
        if values.isna().any():
            continue
        active = values[risky] > float(values["BIL"])
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = filtered_target(base, active)
    return schedule


def schedule_dual_momentum(
    prices: pd.DataFrame, base: pd.Series, months: int = 12, slots: int = 2
) -> dict[pd.Timestamp, pd.Series]:
    monthly = month_end_prices(prices)
    momentum = monthly / monthly.shift(months) - 1.0
    risky = [ticker for ticker in TICKERS if ticker != "BIL" and base[ticker] > 0]
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in monthly.index:
        values = momentum.loc[signal_date, risky + ["BIL"]]
        if values.isna().any():
            continue
        ranked = values[risky].sort_values(ascending=False).head(slots)
        target = pd.Series(0.0, index=TICKERS)
        slot_weight = 1.0 / slots
        for ticker, asset_return in ranked.items():
            if float(asset_return) > float(values["BIL"]):
                target[ticker] += slot_weight
            else:
                target["BIL"] += slot_weight
        target["BIL"] += 1.0 - float(target.sum())
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = target
    return schedule


def schedule_volatility_cap(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    base: pd.Series,
    lookback: int = VOL_LOOKBACK,
    target_vol: float = TARGET_VOL,
) -> dict[pd.Timestamp, pd.Series]:
    # 用固定目标权重的日回报估计基础组合实现波动率。
    base_return = returns.mul(base, axis=1).sum(axis=1)
    realized_vol = base_return.rolling(lookback, min_periods=lookback).std(ddof=1) * math.sqrt(252)
    schedule: dict[pd.Timestamp, pd.Series] = {}
    for signal_date in month_end_prices(prices).index:
        vol = realized_vol.get(signal_date, np.nan)
        if pd.isna(vol) or vol <= 0:
            continue
        scale = min(1.0, target_vol / float(vol))
        target = base * scale
        target["BIL"] += 1.0 - scale
        execute = next_trading_day(prices.index, signal_date)
        if execute is not None:
            schedule[execute] = target
    return schedule


def build_schedule(
    key: str,
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    base: pd.Series,
) -> dict[pd.Timestamp, pd.Series]:
    if key == "buy_hold":
        return {}
    if key == "annual_rebalance":
        return schedule_annual(prices, base)
    if key == "browne_15_35":
        return schedule_annual(prices, base)
    if key == "monthly_rebalance":
        return schedule_monthly_constant(prices, base)
    if key == "sma_10m":
        return schedule_sma_monthly(prices, base, 10)
    if key == "sma_200d":
        return schedule_sma_daily(prices, base, 200)
    if key == "abs_mom_12m":
        return schedule_absolute_momentum(prices, base, 12)
    if key == "dual_mom_top2":
        return schedule_dual_momentum(prices, base, months=12, slots=2)
    if key == "vol_cap_10":
        return schedule_volatility_cap(prices, returns, base)
    raise KeyError(key)


def initial_target_for_start(
    schedule: dict[pd.Timestamp, pd.Series], base: pd.Series, start: pd.Timestamp
) -> pd.Series:
    prior_executions = [date for date in schedule if date < start]
    if not prior_executions:
        return base.copy()
    return schedule[max(prior_executions)].copy()


def simulate(
    returns: pd.DataFrame,
    schedule: dict[pd.Timestamp, pd.Series],
    base: pd.Series,
    costs: dict[str, float],
    start: pd.Timestamp = EVAL_START,
    end: pd.Timestamp = EVAL_END,
    conditional_band: tuple[float, float] | None = None,
) -> SimulationResult:
    period_returns = returns.loc[start:end].copy()
    if period_returns.empty:
        raise AssertionError("评价期无数据")

    initial_target = initial_target_for_start(schedule, base, start)
    cost_vector = pd.Series(costs, index=TICKERS, dtype="float64")
    initial_cost_rate = float((initial_target.abs() * cost_vector).sum())
    holdings = initial_target * (1.0 - initial_cost_rate)
    previous_value = 1.0

    daily_return_records: dict[pd.Timestamp, float] = {}
    equity_records: dict[pd.Timestamp, float] = {}
    cash_weight_records: dict[pd.Timestamp, float] = {}
    turnover_records: dict[pd.Timestamp, float] = {}
    cost_records: dict[pd.Timestamp, float] = {}
    previous_dates = returns.index[returns.index < period_returns.index[0]]
    if len(previous_dates) == 0:
        raise AssertionError("评价起点前缺少收盘日")
    initial_build_date = previous_dates[-1]
    trades: list[dict[str, object]] = [
        {
            "trade_date": initial_build_date.date().isoformat(),
            "event_type": "initial_build",
            # 初始建仓不纳入“评价期内后续单边换手”，
            # 但其成本已从初始净值扣除并在日志中单列。
            "one_way_turnover": 0.0,
            "cost_dollars_per_initial_1": initial_cost_rate,
            "cash_weight_after_trade": float(initial_target["BIL"]),
        }
    ]

    for row_number, (date, asset_returns) in enumerate(period_returns.iterrows()):
        # 如果是 Browne 年检阈值法，是否触发应由上一收盘
        #（即信号日收盘）的漂移权重决定，不用执行日收盘的未知信息。
        signal_date_weights = holdings / previous_value
        holdings = holdings * (1.0 + asset_returns)
        value_before_trade = float(holdings.sum())
        turnover = 0.0
        cost_dollars = initial_cost_rate if row_number == 0 else 0.0

        should_trade = date in schedule
        if should_trade and conditional_band is not None:
            lower, upper = conditional_band
            held_sleeves = base[base > 0].index
            observed = signal_date_weights.loc[held_sleeves]
            should_trade = bool(((observed < lower) | (observed > upper)).any())

        if should_trade:
            target = schedule[date]
            current = holdings / value_before_trade
            absolute_change = (target - current).abs()
            turnover = 0.5 * float(absolute_change.sum())
            cost_rate = float((absolute_change * cost_vector).sum())
            rebalance_cost = value_before_trade * cost_rate
            cost_dollars += rebalance_cost
            value_after_trade = value_before_trade - rebalance_cost
            holdings = target * value_after_trade
            if turnover > 1e-12:
                trades.append(
                    {
                        "trade_date": date.date().isoformat(),
                        "event_type": "rebalance",
                        "one_way_turnover": turnover,
                        "cost_dollars_per_initial_1": rebalance_cost,
                        "cash_weight_after_trade": float(target["BIL"]),
                    }
                )

        value_after_trade = float(holdings.sum())
        daily_return_records[date] = value_after_trade / previous_value - 1.0
        equity_records[date] = value_after_trade
        cash_weight_records[date] = float(holdings["BIL"] / value_after_trade)
        turnover_records[date] = turnover
        cost_records[date] = cost_dollars
        previous_value = value_after_trade

    return SimulationResult(
        daily_return=pd.Series(daily_return_records, name="daily_return"),
        equity=pd.Series(equity_records, name="equity"),
        cash_weight=pd.Series(cash_weight_records, name="cash_weight"),
        turnover=pd.Series(turnover_records, name="one_way_turnover"),
        cost_dollars=pd.Series(cost_records, name="cost_dollars"),
        trade_log=pd.DataFrame(trades),
    )


def maximum_drawdown(equity: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    trough = drawdown.idxmin()
    peak = equity.loc[:trough].idxmax()
    return float(drawdown.loc[trough]), peak, trough


def longest_drawdown_days(equity: pd.Series) -> int:
    underwater = equity < equity.cummax() * (1.0 - 1e-12)
    longest = 0
    current = 0
    for flag in underwater:
        current = current + 1 if bool(flag) else 0
        longest = max(longest, current)
    return longest


def rolling_min_cagr(equity: pd.Series, years: int) -> float:
    monthly = equity.resample("ME").last()
    total = monthly / monthly.shift(12 * years) - 1.0
    annualized = (1.0 + total).pow(1.0 / years) - 1.0
    return float(annualized.min()) if annualized.notna().any() else np.nan


def calculate_metrics(
    result: SimulationResult,
    bil_return: pd.Series,
    gross_result: SimulationResult | None = None,
) -> dict[str, object]:
    daily = result.daily_return.dropna()
    equity = result.equity.loc[daily.index]
    previous_dates = bil_return.index[bil_return.index < daily.index[0]]
    if len(previous_dates) == 0:
        raise AssertionError("评价起点前缺少收盘日")
    initial_value_date = previous_dates[-1]
    elapsed_years = (daily.index[-1] - initial_value_date).days / 365.25
    ending_wealth = float(equity.iloc[-1])
    cagr = ending_wealth ** (1.0 / elapsed_years) - 1.0
    annual_vol = float(daily.std(ddof=1) * math.sqrt(252))
    excess = daily - bil_return.reindex(daily.index).fillna(0.0)
    sharpe = (
        float(excess.mean() / excess.std(ddof=1) * math.sqrt(252))
        if excess.std(ddof=1) > 0
        else np.nan
    )
    downside_deviation = float(np.sqrt(np.mean(np.minimum(excess.to_numpy(), 0.0) ** 2)) * math.sqrt(252))
    sortino = (
        float(excess.mean() * 252 / downside_deviation)
        if downside_deviation > 0
        else np.nan
    )
    equity_for_drawdown = pd.concat(
        [pd.Series([1.0], index=[initial_value_date]), equity]
    )
    max_dd, dd_peak, dd_trough = maximum_drawdown(equity_for_drawdown)
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan

    annual = (1.0 + daily).groupby(daily.index.year).prod() - 1.0
    full_years = annual.loc[(annual.index >= 2009) & (annual.index <= 2025)]
    gross_cagr = np.nan
    ending_cost_drag = np.nan
    if gross_result is not None:
        gross_equity = gross_result.equity.reindex(equity.index)
        gross_ending = float(gross_equity.iloc[-1])
        gross_cagr = gross_ending ** (1.0 / elapsed_years) - 1.0
        ending_cost_drag = 1.0 - ending_wealth / gross_ending

    return {
        "start_date": daily.index[0].date().isoformat(),
        "end_date": daily.index[-1].date().isoformat(),
        "years": elapsed_years,
        "ending_wealth_per_1": ending_wealth,
        "cagr": cagr,
        "arithmetic_mean_annual_return": float(full_years.mean()),
        "annualized_volatility": annual_vol,
        "sharpe_vs_BIL": sharpe,
        "sortino_vs_BIL": sortino,
        "max_drawdown": max_dd,
        "drawdown_peak": dd_peak.date().isoformat(),
        "drawdown_trough": dd_trough.date().isoformat(),
        "calmar": calmar,
        "longest_underwater_trading_days": longest_drawdown_days(equity_for_drawdown),
        "worst_full_calendar_year": int(full_years.idxmin()),
        "worst_full_calendar_return": float(full_years.min()),
        "positive_full_year_ratio": float((full_years > 0).mean()),
        "annual_one_way_turnover": float(result.turnover.sum() / elapsed_years),
        "trade_events": int((result.turnover > 1e-12).sum()),
        "average_BIL_weight": float(result.cash_weight.mean()),
        "cumulative_cost_dollars_per_initial_1": float(result.cost_dollars.sum()),
        "gross_cagr_zero_cost": gross_cagr,
        "cost_drag_cagr_bps": (gross_cagr - cagr) * 10000 if not pd.isna(gross_cagr) else np.nan,
        "ending_wealth_cost_drag": ending_cost_drag,
        "worst_rolling_3y_cagr": rolling_min_cagr(equity, 3),
        "worst_rolling_5y_cagr": rolling_min_cagr(equity, 5),
        "worst_rolling_10y_cagr": rolling_min_cagr(equity, 10),
    }


def period_metrics(daily: pd.Series, bil_return: pd.Series) -> dict[str, float]:
    daily = daily.dropna()
    previous_dates = bil_return.index[bil_return.index < daily.index[0]]
    if len(previous_dates) == 0:
        raise AssertionError("子样本起点前缺少收盘日")
    initial_value_date = previous_dates[-1]
    elapsed_years = (daily.index[-1] - initial_value_date).days / 365.25
    wealth = float((1.0 + daily).prod())
    cagr = wealth ** (1.0 / elapsed_years) - 1.0
    vol = float(daily.std(ddof=1) * math.sqrt(252))
    excess = daily - bil_return.reindex(daily.index).fillna(0.0)
    sharpe = (
        float(excess.mean() / excess.std(ddof=1) * math.sqrt(252))
        if excess.std(ddof=1) > 0
        else np.nan
    )
    equity = pd.concat(
        [pd.Series([1.0], index=[initial_value_date]), (1.0 + daily).cumprod()]
    )
    max_dd, _, _ = maximum_drawdown(equity)
    return {"cagr": cagr, "annualized_volatility": vol, "sharpe_vs_BIL": sharpe, "max_drawdown": max_dd}


def annual_return_rows(
    portfolio: str, strategy: str, daily: pd.Series
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for year, group in daily.groupby(daily.index.year):
        if year == 2008:
            label = "2008-07-01至12-31"
        elif year == 2026:
            label = "2026YTD至07-31"
        else:
            label = str(year)
        rows.append(
            {
                "portfolio": portfolio,
                "strategy": strategy,
                "strategy_cn": STRATEGY_LABELS[strategy],
                "year": int(year),
                "period_label": label,
                "return": float((1.0 + group).prod() - 1.0),
            }
        )
    return rows


def validate_adjusted_close(prices: pd.DataFrame) -> pd.DataFrame:
    # 官方产品页披露的 2025-06-30 至 2026-06-30 市价总回报。
    official = {"SPY": 0.2208, "TLT": 0.0240, "GLD": 0.2085}
    start = pd.Timestamp("2025-06-30")
    end = pd.Timestamp("2026-06-30")
    rows = []
    for ticker, official_return in official.items():
        calculated = float(prices.loc[end, ticker] / prices.loc[start, ticker] - 1.0)
        rows.append(
            {
                "ticker": ticker,
                "period": "2025-06-30至2026-06-30",
                "official_market_value_total_return": official_return,
                "yahoo_adjusted_close_return": calculated,
                "difference_bps": (calculated - official_return) * 10000,
                "within_15bps": abs(calculated - official_return) <= 0.0015,
            }
        )
    return pd.DataFrame(rows)


def run_parameter_sensitivity(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    bil_return: pd.Series,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    specifications: list[tuple[str, list[int], Callable[[pd.Series, int], dict[pd.Timestamp, pd.Series]]]] = [
        ("monthly_SMA", [8, 10, 12], lambda base, value: schedule_sma_monthly(prices, base, value)),
        ("daily_SMA", [150, 200, 250], lambda base, value: schedule_sma_daily(prices, base, value)),
        ("absolute_momentum_months", [6, 9, 12], lambda base, value: schedule_absolute_momentum(prices, base, value)),
    ]
    for portfolio, raw_base in PORTFOLIOS.items():
        base = normalized_weights(raw_base)
        for family, parameters, builder in specifications:
            for parameter in parameters:
                schedule = builder(base, parameter)
                result = simulate(returns, schedule, base, BASE_COSTS)
                metrics = calculate_metrics(result, bil_return)
                rows.append(
                    {
                        "portfolio": portfolio,
                        "family": family,
                        "parameter": parameter,
                        "cagr": metrics["cagr"],
                        "annualized_volatility": metrics["annualized_volatility"],
                        "max_drawdown": metrics["max_drawdown"],
                        "sharpe_vs_BIL": metrics["sharpe_vs_BIL"],
                        "annual_one_way_turnover": metrics["annual_one_way_turnover"],
                    }
                )
    return pd.DataFrame(rows)


def run_cost_sensitivity(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    bil_return: pd.Series,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for portfolio, raw_base in PORTFOLIOS.items():
        base = normalized_weights(raw_base)
        for strategy in STRATEGY_LABELS:
            if strategy == "browne_15_35" and portfolio != "Permanent-25x4":
                continue
            schedule = build_schedule(strategy, prices, returns, base)
            for uniform_bps in [0, 5, 10, 25, 50]:
                costs = {ticker: uniform_bps / 10000 for ticker in TICKERS}
                band = (0.15, 0.35) if strategy == "browne_15_35" else None
                result = simulate(returns, schedule, base, costs, conditional_band=band)
                metrics = calculate_metrics(result, bil_return)
                rows.append(
                    {
                        "portfolio": portfolio,
                        "strategy": strategy,
                        "strategy_cn": STRATEGY_LABELS[strategy],
                        "uniform_one_way_cost_bps": uniform_bps,
                        "cagr": metrics["cagr"],
                        "max_drawdown": metrics["max_drawdown"],
                        "ending_wealth_per_1": metrics["ending_wealth_per_1"],
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    prices = load_adjusted_prices()
    returns = prices.pct_change(fill_method=None).dropna(how="any")
    bil_return = returns["BIL"]

    summary_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    subperiod_rows: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    result_cache: dict[tuple[str, str], SimulationResult] = {}

    for portfolio, raw_base in PORTFOLIOS.items():
        base = normalized_weights(raw_base)
        for strategy in STRATEGY_LABELS:
            if strategy == "browne_15_35" and portfolio != "Permanent-25x4":
                continue
            schedule = build_schedule(strategy, prices, returns, base)
            band = (0.15, 0.35) if strategy == "browne_15_35" else None
            result = simulate(returns, schedule, base, BASE_COSTS, conditional_band=band)
            gross = simulate(
                returns,
                schedule,
                base,
                {ticker: 0.0 for ticker in TICKERS},
                conditional_band=band,
            )
            result_cache[(portfolio, strategy)] = result
            metrics = calculate_metrics(result, bil_return, gross)
            metrics.update(
                {
                    "portfolio": portfolio,
                    "strategy": strategy,
                    "strategy_cn": STRATEGY_LABELS[strategy],
                }
            )
            summary_rows.append(metrics)
            annual_rows.extend(annual_return_rows(portfolio, strategy, result.daily_return))

            for period_name, period_start, period_end in [
                ("2008-07-01_to_2017-12-29", pd.Timestamp("2008-07-01"), pd.Timestamp("2017-12-29")),
                ("2018-01-02_to_2026-07-31", pd.Timestamp("2018-01-02"), EVAL_END),
            ]:
                subset = result.daily_return.loc[period_start:period_end]
                period = period_metrics(subset, bil_return)
                period.update(
                    {
                        "portfolio": portfolio,
                        "strategy": strategy,
                        "strategy_cn": STRATEGY_LABELS[strategy],
                        "period": period_name,
                    }
                )
                subperiod_rows.append(period)

            if not result.trade_log.empty:
                trade_log = result.trade_log.copy()
                trade_log.insert(0, "strategy", strategy)
                trade_log.insert(0, "portfolio", portfolio)
                trade_frames.append(trade_log)

    summary = pd.DataFrame(summary_rows)
    # 与各自的“年度再平衡”基准比较，不混用股票指数作唯一基准。
    annual_baseline = summary.loc[
        summary["strategy"] == "annual_rebalance",
        ["portfolio", "cagr", "max_drawdown"],
    ].rename(columns={"cagr": "baseline_cagr", "max_drawdown": "baseline_max_drawdown"})
    summary = summary.merge(annual_baseline, on="portfolio", how="left")
    summary["excess_cagr_vs_annual_rebalance"] = summary["cagr"] - summary["baseline_cagr"]
    summary["max_drawdown_change_vs_annual_rebalance"] = (
        summary["max_drawdown"] - summary["baseline_max_drawdown"]
    )

    annual = pd.DataFrame(annual_rows)
    subperiod = pd.DataFrame(subperiod_rows)
    trades = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    parameter_sensitivity = run_parameter_sensitivity(prices, returns, bil_return)
    cost_sensitivity = run_cost_sensitivity(prices, returns, bil_return)
    validation = validate_adjusted_close(prices)

    summary.to_csv(HERE / "backtest_summary.csv", index=False, encoding="utf-8")
    annual.to_csv(HERE / "backtest_annual_returns.csv", index=False, encoding="utf-8")
    subperiod.to_csv(HERE / "backtest_subperiods.csv", index=False, encoding="utf-8")
    trades.to_csv(HERE / "backtest_trade_log.csv", index=False, encoding="utf-8")
    parameter_sensitivity.to_csv(HERE / "backtest_parameter_sensitivity.csv", index=False, encoding="utf-8")
    cost_sensitivity.to_csv(HERE / "backtest_cost_sensitivity.csv", index=False, encoding="utf-8")
    validation.to_csv(HERE / "backtest_data_validation.csv", index=False, encoding="utf-8")

    print(f"data_window={prices.index.min().date()}..{prices.index.max().date()} rows={len(prices)}")
    print(f"evaluation_window={EVAL_START.date()}..{EVAL_END.date()} rows={len(returns.loc[EVAL_START:EVAL_END])}")
    print("\nKEY SUMMARY (%)")
    display_columns = [
        "portfolio",
        "strategy_cn",
        "cagr",
        "annualized_volatility",
        "max_drawdown",
        "sharpe_vs_BIL",
        "average_BIL_weight",
        "annual_one_way_turnover",
    ]
    printable = summary[display_columns].copy()
    for column in ["cagr", "annualized_volatility", "max_drawdown", "average_BIL_weight", "annual_one_way_turnover"]:
        printable[column] = printable[column] * 100
    print(printable.to_string(index=False, float_format=lambda value: f"{value:.2f}"))
    print("\nDATA VALIDATION")
    print(validation.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    if not bool(validation["within_15bps"].all()):
        raise AssertionError("复权价与官方市价总回报差异超过 15bp")


if __name__ == "__main__":
    main()
