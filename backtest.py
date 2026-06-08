"""
Backtesting — corre el pipeline sobre mercados históricos resueltos
y genera reporte de performance con paper orders.

Uso:
    python backtest.py
"""
import logging
import sys
from datetime import datetime
from typing import List, Tuple

import layer2_filter     as capa2
import layer3_modeling   as capa3
import layer4_montecarlo as capa4
import layer5_signal     as capa5
import layer6_registry   as capa6
import layer7_feedback   as capa7
import layer8_execution  as capa8
from historical_data import HISTORICAL_MARKETS
from models import Market, NewsItem, DeltaSignal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-20s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("backtest")


def run_backtest():
    print(f"\n{'='*65}")
    print(f"  BACKTESTING — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Capital inicial: ${capa8.STARTING_CAPITAL:,.0f} USDC")
    print(f"  Mercados históricos: {len(HISTORICAL_MARKETS)}")
    print(f"{'='*65}\n")

    capa6.initialize()
    capa8.initialize()
    weights = capa7.get_weights()

    results: List[Tuple[DeltaSignal, str]] = []   # (signal, actual_outcome)

    for i, (market, news, actual_outcome) in enumerate(HISTORICAL_MARKETS, 1):
        print(f"\n[{i}/{len(HISTORICAL_MARKETS)}] {market.question[:60]}")
        print(f"  Precio mercado: {market.p_yes:.2f} | Outcome real: {actual_outcome}")
        print(f"  Noticias: {len(news)} items")

        filtered = capa2.filter_signals([market], news)
        if not filtered:
            print(f"  → Sin señales relevantes para este mercado")
            continue

        for fs in filtered:
            crowd    = capa3.simulate_crowd_reaction(fs)
            bayesian = capa3.get_bayesian_prior(market.category, weights)
            mc       = capa4.run_monte_carlo(fs, crowd, bayesian)
            delta    = capa5.compute_delta_signal(fs, crowd, mc, bayesian)

            if not delta:
                print(f"  → Delta bajo umbral, sin señal")
                continue

            capa6.save_signal(delta)
            order = capa8.open_paper_order(delta)

            if order:
                capa8.resolve_paper_order(order.order_id, actual_outcome)
                results.append((delta, actual_outcome))

    # Feedback loop post-backtest
    capa7.run()

    print_report(results)


def print_report(results: List[Tuple[DeltaSignal, str]]):
    perf = capa8.performance_report()
    orders = capa8.get_all_orders()
    resolved = [o for o in orders if o["status"] == "resolved"]

    print(f"\n{'='*65}")
    print(f"  REPORTE DE BACKTESTING")
    print(f"{'='*65}")
    print(f"\n  Capital inicial : ${perf['starting_capital']:>10,.2f} USDC")
    print(f"  Capital final   : ${perf['portfolio_value']:>10,.2f} USDC")
    print(f"  P&L total       : ${perf['total_pnl']:>+10,.2f} USDC")
    print(f"  ROI             : {perf['roi_pct']:>+9.1f}%")
    print(f"\n  Órdenes totales : {perf['total_orders']}")
    print(f"  Resueltas       : {perf['resolved']}")
    print(f"  Win rate        : {(perf['win_rate'] or 0)*100:.1f}%")
    if perf.get("avg_win") is not None:
        print(f"  Avg ganancia    : ${perf.get('avg_win', 0):>+.2f} USDC")
        print(f"  Avg pérdida     : ${perf.get('avg_loss', 0):>+.2f} USDC")
        pf = perf.get("profit_factor", 0)
        print(f"  Profit factor   : {pf:.2f}x" if pf != float('inf') else "  Profit factor   : inf (sin pérdidas)")

    print(f"\n{'-'*65}")
    print(f"  DETALLE POR ORDEN")
    print(f"{'-'*65}")

    for o in resolved:
        won = o["pnl_usdc"] > 0
        icon = "OK" if won else "XX"
        print(f"""
  [{icon}] {o['order_id']} — {o['action']}
  Mercado  : {o['market_question'][:63]}
  Categoría: {o['category']}
  Entrada  : {o['entry_price']:.3f} | P_sim: {o['p_simulated']:.3f} | Δ: {o['delta']:+.3f}
  Invertido: ${o['usdc_invested']:.2f} USDC | Acciones: {o['shares']:.2f}
  Outcome  : {o['outcome']} → P&L: ${o['pnl_usdc']:+.2f} ({o['pnl_pct']:+.1f}%)
  {'-'*63}""")

    # Categorías con mejor performance
    if resolved:
        print(f"\n  PERFORMANCE POR CATEGORÍA")
        print(f"  {'-'*40}")
        by_cat: dict = {}
        for o in resolved:
            cat = o["category"]
            by_cat.setdefault(cat, {"wins": 0, "total": 0, "pnl": 0.0})
            by_cat[cat]["total"] += 1
            by_cat[cat]["pnl"]   += o["pnl_usdc"]
            if o["pnl_usdc"] > 0:
                by_cat[cat]["wins"] += 1
        for cat, d in sorted(by_cat.items(), key=lambda x: x[1]["pnl"], reverse=True):
            wr = d["wins"] / d["total"] * 100 if d["total"] else 0
            print(f"  {cat:12s} | {d['wins']}/{d['total']} ({wr:.0f}%) | P&L: ${d['pnl']:+.2f}")

    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    run_backtest()
