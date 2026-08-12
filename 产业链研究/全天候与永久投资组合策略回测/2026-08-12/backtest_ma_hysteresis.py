"""10-month moving-average hysteresis backtest for the two archived portfolios.

This is an incremental companion to ``backtest_portfolios.py``.  It deliberately
imports the archived prices, costs, simulator, and metric definitions from that
file so that the new results stay comparable with the existing report outputs.

Signal and execution convention
-------------------------------
* Observe each sleeve's adjusted close and 10-month SMA at month-end ``t``.
* If inactive, turn on only when price > SMA * (1 + buffer).
* If active, turn off only when price < SMA * (1 - buffer).
* Inside the band (including equality), retain the prior state.
* Submit a whole-portfolio target only after a state change, at calendar
  year-end, or at the first valid signal used to initialize the state machine.
* Execute at the next trading day's close (``t+1``).  The new target therefore
  affects returns beginning with the following close-to-close interval
  (``t+2``), matching the simulator's timing convention.
* Inactive sleeve weights move to BIL; there is no shorting or leverage.

The state machine starts with every non-BIL sleeve inactive before its first
valid 10-month observation.  Initial portfolio construction at the evaluation
boundary uses the last target actually executable before the boundary.  Its
transaction cost is deducted from initial wealth and reported separately; its
turnover is not included in evaluation-period annual turnover, consistent with
``backtest_portfolios.py``.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

import backtest_portfolios as core


SMA_MONTHS = 10
BUFFERS = (0.00, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20)
STRATEGY = "sma_10m_hysteresis"
STRATEGY_CN = "10月均线缓冲带（状态变化/年末调仓）"


@dataclass(frozen=True)
class HysteresisSchedule:
    targets: dict[pd.Timestamp, pd.Series]
    events: pd.DataFrame
    risky_sleeves: tuple[str, ...]
    latest_signals: pd.DataFrame


def _state_text(state: dict[str, bool] | pd.Series) -> str:
    """Return a stable, spreadsheet-friendly state representation."""
    return ";".join(f"{ticker}={'on' if bool(state[ticker]) else 'off'}" for ticker in state)


def _weights_json(weights: pd.Series) -> str:
    return json.dumps(
        {ticker: round(float(weights[ticker]), 12) for ticker in core.TICKERS},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def build_hysteresis_schedule(
    prices: pd.DataFrame,
    base: pd.Series,
    buffer: float,
    months: int = SMA_MONTHS,
) -> HysteresisSchedule:
    """Build executable targets and an auditable signal-event table."""
    if buffer < 0 or buffer >= 1:
        raise ValueError(f"buffer must be in [0, 1), got {buffer}")

    monthly = core.month_end_prices(prices)
    moving_average = monthly.rolling(window=months, min_periods=months).mean()
    risky = tuple(
        ticker for ticker in core.TICKERS if ticker != "BIL" and float(base[ticker]) > 0
    )
    state = {ticker: False for ticker in risky}
    initialized = False
    schedule: dict[pd.Timestamp, pd.Series] = {}
    event_rows: list[dict[str, object]] = []
    latest_prior_state = state.copy()

    for signal_date in monthly.index:
        sma_row = moving_average.loc[signal_date, list(risky)]
        if sma_row.isna().any():
            continue

        prior = state.copy()
        prices_row = monthly.loc[signal_date, list(risky)]
        transitions: list[str] = []
        for ticker in risky:
            price = float(prices_row[ticker])
            sma = float(sma_row[ticker])
            if not state[ticker] and price > sma * (1.0 + buffer):
                state[ticker] = True
                transitions.append(f"{ticker}:off->on")
            elif state[ticker] and price < sma * (1.0 - buffer):
                state[ticker] = False
                transitions.append(f"{ticker}:on->off")
        latest_prior_state = prior

        is_year_end = signal_date.month == 12
        is_initialization = not initialized
        has_state_change = state != prior
        if not (is_initialization or has_state_change or is_year_end):
            initialized = True
            continue

        execute_date = core.next_trading_day(prices.index, signal_date)
        initialized = True
        if execute_date is None:
            continue

        target = core.filtered_target(base, pd.Series(state, dtype="bool"))
        reasons: list[str] = []
        if is_initialization:
            reasons.append("initialization")
        if has_state_change:
            reasons.append("state_change")
        if is_year_end:
            reasons.append("year_end_rebalance")
        reason = "+".join(reasons)

        if execute_date in schedule:
            raise AssertionError(f"duplicate execution date: {execute_date.date()}")
        schedule[execute_date] = target
        row: dict[str, object] = {
            "signal_date": signal_date.date().isoformat(),
            "execute_date": execute_date.date().isoformat(),
            "trigger_reason": reason,
            "state_changed": has_state_change,
            "changed_sleeves": ";".join(transitions),
            "state_before": _state_text(prior),
            "state_after": _state_text(state),
            "target_weights": _weights_json(target),
        }
        for ticker in core.TICKERS:
            row[f"target_{ticker}"] = float(target[ticker])
        event_rows.append(row)

    if not schedule:
        raise AssertionError("hysteresis schedule is empty")
    events = pd.DataFrame(event_rows)
    latest_signal_date = moving_average.loc[:, list(risky)].dropna(how="any").index[-1]
    latest_execute_date = core.next_trading_day(prices.index, latest_signal_date)
    latest_rows: list[dict[str, object]] = []
    for ticker in risky:
        price = float(monthly.loc[latest_signal_date, ticker])
        sma = float(moving_average.loc[latest_signal_date, ticker])
        upper = sma * (1.0 + buffer)
        lower = sma * (1.0 - buffer)
        is_active = bool(state[ticker])
        transitioned = bool(state[ticker]) != bool(latest_prior_state[ticker])
        latest_rows.append(
            {
                "signal_date": latest_signal_date.date().isoformat(),
                "sleeve": ticker,
                "price": price,
                "sma_10m": sma,
                "distance": price / sma - 1.0,
                "distance_pct": (price / sma - 1.0) * 100.0,
                "active": is_active,
                "active_semantics": "target state after latest signal; may be pending if no execute date",
                "position_active_at_signal_close": bool(latest_prior_state[ticker]),
                "execute_date": (
                    latest_execute_date.date().isoformat()
                    if latest_execute_date is not None
                    else ""
                ),
                "pending_execution_outside_sample": transitioned and latest_execute_date is None,
                "upper_entry_threshold": upper,
                "lower_exit_threshold": lower,
                "reentry_threshold_if_inactive": upper if not is_active else np.nan,
                "signal_action": (
                    "turn_on_pending_next_available_close_outside_sample"
                    if transitioned and is_active and latest_execute_date is None
                    else "turn_off_pending_next_available_close_outside_sample"
                    if transitioned and not is_active and latest_execute_date is None
                    else "turn_on_next_close"
                    if transitioned and is_active
                    else "turn_off_next_close"
                    if transitioned and not is_active
                    else "hold_active"
                    if is_active
                    else "hold_inactive"
                ),
            }
        )
    latest_signals = pd.DataFrame(latest_rows)
    return HysteresisSchedule(schedule, events, risky, latest_signals)


def _annual_return_rows(
    portfolio: str,
    buffer: float,
    daily: pd.Series,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for year, group in daily.groupby(daily.index.year):
        if year == 2008:
            period_label = "2008-07-01至12-31"
        elif year == 2026:
            period_label = "2026YTD至07-31"
        else:
            period_label = str(year)
        rows.append(
            {
                "portfolio": portfolio,
                "strategy": STRATEGY,
                "strategy_cn": STRATEGY_CN,
                "sma_months": SMA_MONTHS,
                "buffer": buffer,
                "buffer_pct": buffer * 100.0,
                "year": int(year),
                "period_label": period_label,
                "return": float((1.0 + group).prod() - 1.0),
            }
        )
    return rows


def _initial_context(
    built: HysteresisSchedule,
    base: pd.Series,
) -> dict[str, object]:
    prior_dates = [date for date in built.targets if date < core.EVAL_START]
    if not prior_dates:
        raise AssertionError(
            "no executable hysteresis target exists before the evaluation boundary"
        )
    last_execute = max(prior_dates)
    target = built.targets[last_execute]
    event = built.events.loc[
        built.events["execute_date"] == last_execute.date().isoformat()
    ].iloc[-1]
    previous_prices = core.EVAL_START - pd.Timedelta(days=1)
    initial_cost_rate = float(
        (target.abs() * pd.Series(core.BASE_COSTS, index=core.TICKERS)).sum()
    )
    return {
        "initial_state_rule": "all risky sleeves inactive before first valid 10m SMA signal",
        "initial_target_effective_from": last_execute.date().isoformat(),
        "initial_target_signal_date": event["signal_date"],
        "initial_state_at_evaluation_prior_close": event["state_after"],
        "initial_target_weights": _weights_json(target),
        "initial_build_reference_close": previous_prices.date().isoformat(),
        "initial_build_cost_dollars_per_initial_1": initial_cost_rate,
        "initial_build_turnover_convention": "excluded from evaluation-period turnover",
    }


def _enrich_trade_log(
    portfolio: str,
    buffer: float,
    result: core.SimulationResult,
    built: HysteresisSchedule,
    initial: dict[str, object],
) -> pd.DataFrame:
    trades = result.trade_log.copy()
    events = built.events.copy()
    events = events.rename(columns={"execute_date": "trade_date"})
    keep = [
        "trade_date",
        "signal_date",
        "trigger_reason",
        "state_changed",
        "changed_sleeves",
        "state_before",
        "state_after",
        "target_weights",
    ] + [f"target_{ticker}" for ticker in core.TICKERS]
    trades = trades.merge(events[keep], on="trade_date", how="left", validate="many_to_one")

    initial_mask = trades["event_type"].eq("initial_build")
    trades.loc[initial_mask, "signal_date"] = str(initial["initial_target_signal_date"])
    trades.loc[initial_mask, "trigger_reason"] = "initial_build_at_evaluation_boundary"
    trades.loc[initial_mask, "state_after"] = str(
        initial["initial_state_at_evaluation_prior_close"]
    )
    trades.loc[initial_mask, "target_weights"] = str(initial["initial_target_weights"])
    initial_weights = json.loads(str(initial["initial_target_weights"]))
    for ticker in core.TICKERS:
        trades.loc[initial_mask, f"target_{ticker}"] = float(initial_weights[ticker])

    trades.insert(0, "buffer_pct", buffer * 100.0)
    trades.insert(0, "buffer", buffer)
    trades.insert(0, "sma_months", SMA_MONTHS)
    trades.insert(0, "strategy_cn", STRATEGY_CN)
    trades.insert(0, "strategy", STRATEGY)
    trades.insert(0, "portfolio", portfolio)
    trades["initial_cost_included"] = initial_mask
    return trades


def _run_self_checks(
    prices: pd.DataFrame,
    summaries: pd.DataFrame,
    annual: pd.DataFrame,
    subperiods: pd.DataFrame,
    latest_signals: pd.DataFrame,
    trades: pd.DataFrame,
    built_cache: dict[tuple[str, float], HysteresisSchedule],
) -> None:
    expected_specs = len(core.PORTFOLIOS) * len(BUFFERS)
    if len(summaries) != expected_specs:
        raise AssertionError(f"summary rows {len(summaries)} != {expected_specs}")
    if summaries[["portfolio", "buffer"]].duplicated().any():
        raise AssertionError("duplicate portfolio/buffer summary rows")
    if set(summaries["buffer"].round(10)) != set(np.round(BUFFERS, 10)):
        raise AssertionError("buffer grid is incomplete")
    if not (summaries["initial_cost_included"] == True).all():  # noqa: E712
        raise AssertionError("initial-cost flag must be true for every specification")
    if (summaries["trade_events_including_initial"] != summaries["trade_events"] + 1).any():
        raise AssertionError("trade-event count convention is inconsistent")
    if not np.isfinite(
        summaries[
            [
                "cagr",
                "annualized_volatility",
                "sharpe_vs_BIL",
                "sortino_vs_BIL",
                "max_drawdown",
                "calmar",
                "annual_one_way_turnover",
                "cumulative_cost_dollars_per_initial_1",
                "average_BIL_weight",
                "worst_rolling_3y_cagr",
                "worst_rolling_5y_cagr",
                "worst_rolling_10y_cagr",
            ]
        ].to_numpy(dtype=float)
    ).all():
        raise AssertionError("required summary metrics contain non-finite values")

    expected_years = set(range(2008, 2027))
    for (portfolio, buffer), group in annual.groupby(["portfolio", "buffer"]):
        if set(group["year"]) != expected_years:
            raise AssertionError(f"annual rows incomplete for {portfolio}, {buffer}")

    if len(subperiods) != expected_specs * 2:
        raise AssertionError("subperiod output does not contain two fixed periods per specification")
    required_periods = {"2008-07-01_to_2017-12-29", "2018-01-02_to_2026-07-31"}
    for (portfolio, buffer), group in subperiods.groupby(["portfolio", "buffer"]):
        if set(group["period"]) != required_periods:
            raise AssertionError(f"subperiod split incomplete for {portfolio}, {buffer}")
    if len(latest_signals) != sum(
        len(built.risky_sleeves) for built in built_cache.values()
    ):
        raise AssertionError("latest-signal sleeve count is incomplete")
    if not latest_signals["signal_date"].eq(core.EVAL_END.date().isoformat()).all():
        raise AssertionError("latest-signal output is not anchored to the evaluation end date")
    changed_latest = (
        latest_signals["active"] != latest_signals["position_active_at_signal_close"]
    )
    if not latest_signals.loc[changed_latest, "pending_execution_outside_sample"].all():
        raise AssertionError("latest state transition must be marked pending outside sample")
    if latest_signals.loc[changed_latest, "execute_date"].ne("").any():
        raise AssertionError("latest out-of-sample pending signal unexpectedly has an execute date")
    inactive = latest_signals.loc[~latest_signals["active"]]
    if inactive["reentry_threshold_if_inactive"].isna().any():
        raise AssertionError("an inactive sleeve is missing its re-entry threshold")

    if trades.empty or not trades["event_type"].eq("initial_build").any():
        raise AssertionError("trade log is missing initial builds")
    if trades["signal_date"].isna().any():
        raise AssertionError("a trade-log row lacks its source signal date")

    for (portfolio, buffer), built in built_cache.items():
        for execute_date, target in built.targets.items():
            event = built.events.loc[
                built.events["execute_date"] == execute_date.date().isoformat()
            ].iloc[-1]
            signal_date = pd.Timestamp(event["signal_date"])
            expected_execute = core.next_trading_day(prices.index, signal_date)
            if execute_date != expected_execute or execute_date <= signal_date:
                raise AssertionError(f"timing error for {portfolio}, {buffer}, {signal_date}")
            if not math.isclose(float(target.sum()), 1.0, abs_tol=1e-10):
                raise AssertionError("target weights do not sum to one")
            if (target < -1e-12).any() or (target > 1.0 + 1e-12).any():
                raise AssertionError("shorting or leverage detected")


def main() -> None:
    prices = core.load_adjusted_prices()
    returns = prices.pct_change(fill_method=None).dropna(how="any")
    bil_return = returns["BIL"]
    zero_costs = {ticker: 0.0 for ticker in core.TICKERS}

    summary_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    subperiod_rows: list[dict[str, object]] = []
    latest_signal_frames: list[pd.DataFrame] = []
    trade_frames: list[pd.DataFrame] = []
    built_cache: dict[tuple[str, float], HysteresisSchedule] = {}

    for portfolio, raw_base in core.PORTFOLIOS.items():
        base = core.normalized_weights(raw_base)
        for buffer in BUFFERS:
            built = build_hysteresis_schedule(prices, base, buffer)
            built_cache[(portfolio, buffer)] = built
            initial = _initial_context(built, base)
            if max(built.targets) > core.EVAL_END:
                raise AssertionError("an executable target extends beyond the evaluation end")
            result = core.simulate(returns, built.targets, base, core.BASE_COSTS)
            gross = core.simulate(returns, built.targets, base, zero_costs)
            metrics = core.calculate_metrics(result, bil_return, gross)

            in_sample_events = built.events.loc[
                pd.to_datetime(built.events["execute_date"]).between(
                    core.EVAL_START, core.EVAL_END
                )
            ]
            metrics.update(
                {
                    "portfolio": portfolio,
                    "strategy": STRATEGY,
                    "strategy_cn": STRATEGY_CN,
                    "sma_months": SMA_MONTHS,
                    "buffer": buffer,
                    "buffer_pct": buffer * 100.0,
                    "entry_rule": "P > SMA10*(1+buffer)",
                    "exit_rule": "P < SMA10*(1-buffer)",
                    "inside_band_rule": "retain prior sleeve state",
                    "rebalance_rule": "state change or calendar year-end; execute next trading-day close",
                    "inactive_weight_destination": "BIL",
                    "state_change_signal_events": int(in_sample_events["state_changed"].sum()),
                    "scheduled_target_events": int(len(in_sample_events)),
                    "year_end_target_events": int(
                        in_sample_events["trigger_reason"].str.contains("year_end_rebalance").sum()
                    ),
                    "trade_events_including_initial": int(metrics["trade_events"]) + 1,
                    "initial_cost_included": True,
                    **initial,
                }
            )
            summary_rows.append(metrics)
            annual_rows.extend(_annual_return_rows(portfolio, buffer, result.daily_return))
            for period_name, period_start, period_end in [
                (
                    "2008-07-01_to_2017-12-29",
                    pd.Timestamp("2008-07-01"),
                    pd.Timestamp("2017-12-29"),
                ),
                (
                    "2018-01-02_to_2026-07-31",
                    pd.Timestamp("2018-01-02"),
                    core.EVAL_END,
                ),
            ]:
                period = core.period_metrics(
                    result.daily_return.loc[period_start:period_end], bil_return
                )
                period.update(
                    {
                        "portfolio": portfolio,
                        "strategy": STRATEGY,
                        "strategy_cn": STRATEGY_CN,
                        "sma_months": SMA_MONTHS,
                        "buffer": buffer,
                        "buffer_pct": buffer * 100.0,
                        "period": period_name,
                    }
                )
                subperiod_rows.append(period)
            latest = built.latest_signals.copy()
            latest.insert(0, "buffer_pct", buffer * 100.0)
            latest.insert(0, "buffer", buffer)
            latest.insert(0, "sma_months", SMA_MONTHS)
            latest.insert(0, "strategy_cn", STRATEGY_CN)
            latest.insert(0, "strategy", STRATEGY)
            latest.insert(0, "portfolio", portfolio)
            latest_signal_frames.append(latest)
            trade_frames.append(
                _enrich_trade_log(portfolio, buffer, result, built, initial)
            )

    summary = pd.DataFrame(summary_rows)
    annual = pd.DataFrame(annual_rows)
    subperiods = pd.DataFrame(subperiod_rows)
    latest_signals = pd.concat(latest_signal_frames, ignore_index=True)
    trades = pd.concat(trade_frames, ignore_index=True)
    _run_self_checks(
        prices, summary, annual, subperiods, latest_signals, trades, built_cache
    )

    summary_path = core.HERE / "backtest_ma_hysteresis_summary.csv"
    annual_path = core.HERE / "backtest_ma_hysteresis_annual_returns.csv"
    subperiods_path = core.HERE / "backtest_ma_hysteresis_subperiods.csv"
    latest_signals_path = core.HERE / "backtest_ma_hysteresis_latest_signals.csv"
    trades_path = core.HERE / "backtest_ma_hysteresis_trade_log.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8")
    annual.to_csv(annual_path, index=False, encoding="utf-8")
    subperiods.to_csv(subperiods_path, index=False, encoding="utf-8")
    latest_signals.to_csv(latest_signals_path, index=False, encoding="utf-8")
    trades.to_csv(trades_path, index=False, encoding="utf-8")

    display = summary[
        [
            "portfolio",
            "buffer_pct",
            "cagr",
            "annualized_volatility",
            "sharpe_vs_BIL",
            "sortino_vs_BIL",
            "max_drawdown",
            "calmar",
            "trade_events",
            "annual_one_way_turnover",
            "cumulative_cost_dollars_per_initial_1",
            "average_BIL_weight",
            "worst_rolling_3y_cagr",
            "worst_rolling_5y_cagr",
            "worst_rolling_10y_cagr",
        ]
    ].copy()
    print(
        display.to_string(
            index=False,
            float_format=lambda value: f"{value:.6f}",
        )
    )
    print(
        f"\nself_check=PASS summary_rows={len(summary)} annual_rows={len(annual)} "
        f"subperiod_rows={len(subperiods)} latest_signal_rows={len(latest_signals)} "
        f"trade_rows={len(trades)}"
    )
    print(
        "wrote="
        + ",".join(
            path.name
            for path in [
                summary_path,
                annual_path,
                subperiods_path,
                latest_signals_path,
                trades_path,
            ]
        )
    )


if __name__ == "__main__":
    main()
