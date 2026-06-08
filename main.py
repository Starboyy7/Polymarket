"""Orchestrador principal — pipeline en vivo con mercados reales de Polymarket."""
import logging
import sys
from datetime import datetime
from typing import List

import layer1_ingestion  as capa1
import layer2_filter     as capa2
import layer3_modeling   as capa3
import layer4_montecarlo as capa4
import layer5_signal     as capa5
import layer6_registry   as capa6
import layer7_feedback   as capa7
import layer8_execution  as capa8
from models import DeltaSignal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-20s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("main")


def run_pipeline() -> List[DeltaSignal]:
    logger.info("=" * 65)
    logger.info(f"PIPELINE LIVE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 65)

    capa6.initialize()
    capa8.initialize()
    weights = capa7.get_weights()

    # -- Capa 1: Ingesta real (Polymarket + GDELT + RSS + Reddit) --
    markets, news = capa1.ingest_all()
    if not markets:
        logger.warning("Sin mercados disponibles. Abortando.")
        return []

    # -- Capa 2: Filtrado LLM --------------------------------------
    signals = capa2.filter_signals(markets, news)
    if not signals:
        logger.info("Sin señales relevantes. Pipeline completo.")
        return []

    delta_signals: List[DeltaSignal] = []

    for fs in signals:
        # -- Capa 3: Crowd + Bayesian ------------------------------
        crowd    = capa3.simulate_crowd_reaction(fs)
        bayesian = capa3.get_bayesian_prior(fs.market.category, weights)

        # -- Capa 4: Monte Carlo -----------------------------------
        mc = capa4.run_monte_carlo(fs, crowd, bayesian)

        # -- Capa 5: Señal delta -----------------------------------
        delta = capa5.compute_delta_signal(fs, crowd, mc, bayesian)
        if not delta:
            continue

        # -- Capa 6: Registro --------------------------------------
        capa6.save_signal(delta)

        # -- Capa 8: Paper order -----------------------------------
        order = capa8.open_paper_order(delta)
        if order:
            delta_signals.append(delta)

    # -- Capa 7: Feedback loop ------------------------------------
    capa7.run()

    logger.info(f"PIPELINE COMPLETE — {len(delta_signals)} orden(es) paper abierta(s)")
    return delta_signals


def print_report(signals: List[DeltaSignal]):
    orders = capa8.get_all_orders()
    open_orders = [o for o in orders if o["status"] == "open"]
    perf = capa8.performance_report()

    print(f"\n{'='*65}")
    print(f"  SEÑALES EN VIVO — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}")
    print(f"\n  Capital disponible : ${perf['cash']:>10,.2f} USDC")
    print(f"  Ordenes abiertas   : {len(open_orders)}")

    if not signals:
        print("\n  Sin señales en este ciclo.\n")
        return

    print(f"\n{'-'*65}")
    for s in signals:
        if s.action == "BUY_YES":
            precio_entrada = s.p_polymarket
            accion = f"COMPRAR YES  a {precio_entrada*100:.0f}c  (apostar a que SI ocurre)"
        else:
            precio_entrada = 1.0 - s.p_polymarket
            accion = f"COMPRAR NO   a {precio_entrada*100:.0f}c  (apostar a que NO ocurre)"

        edge = abs(s.delta) * 100
        url_line = f"\n  URL        : {s.market.url}" if s.market.url else ""
        print(f"""
  [{s.signal_id}]
  Mercado    : {s.market.question[:65]}{url_line}
  Categoria  : {s.market.category}
  -------------------------------------------------------
  SENAL      : {accion}
  Edge       : {edge:.1f}pp de ventaja | Confianza: {s.confidence:.2f}
  -------------------------------------------------------
  P_mercado  : {s.p_polymarket*100:.1f}%   (precio actual en Polymarket)
  P_modelo   : {s.p_simulated*100:.1f}%   (lo que nuestro sistema estima)
  Delta      : {s.delta*100:+.1f}pp
  Narrativa  : {s.crowd_signal.narrative[:120]}
  Fuente     : {s.filtered_signal.news.source} — {s.filtered_signal.news.title[:55]}
  {'-'*63}""")

    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    import sys
    demo_mode = "--demo" in sys.argv

    if demo_mode:
        import demo_data
        capa6.initialize()
        capa8.initialize()
        logger.info("Modo DEMO: usando datos de muestra")
        signals = []
        weights = capa7.get_weights()
        for fs in capa2.filter_signals(demo_data.MARKETS, demo_data.NEWS):
            crowd    = capa3.simulate_crowd_reaction(fs)
            bayesian = capa3.get_bayesian_prior(fs.market.category, weights)
            mc       = capa4.run_monte_carlo(fs, crowd, bayesian)
            delta    = capa5.compute_delta_signal(fs, crowd, mc, bayesian)
            if delta:
                capa6.save_signal(delta)
                capa8.open_paper_order(delta)
                signals.append(delta)
        capa7.run()
    else:
        signals = run_pipeline()

    print_report(signals)
