"""Orchestrador principal — ejecuta el pipeline de 7 capas."""
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
from models import DeltaSignal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-20s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("main")


def run_pipeline() -> List[DeltaSignal]:
    logger.info("=" * 65)
    logger.info(f"PIPELINE START — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 65)

    # ── Capa 1: Ingesta ──────────────────────────────────────────────
    markets, news = capa1.ingest_all()
    if not markets:
        logger.warning("Sin mercados disponibles. Abortando.")
        return []

    # ── Capa 2: Filtrado Claude ───────────────────────────────────────
    signals = capa2.filter_signals(markets, news)
    if not signals:
        logger.info("Sin señales relevantes. Pipeline completo.")
        return []

    # ── Capa 7 (pre-loop): obtener pesos actuales ─────────────────────
    weights = capa7.get_weights()

    delta_signals: List[DeltaSignal] = []

    for fs in signals:
        cat = fs.market.category

        # ── Capa 3A: Simulación de crowd ──────────────────────────────
        crowd = capa3.simulate_crowd_reaction(fs)

        # ── Capa 3B: Base rates bayesianas ────────────────────────────
        bayesian = capa3.get_bayesian_prior(cat, weights)

        # ── Capa 4: Monte Carlo ───────────────────────────────────────
        mc = capa4.run_monte_carlo(fs, crowd, bayesian)

        # ── Capa 5: Señal delta ───────────────────────────────────────
        delta = capa5.compute_delta_signal(fs, crowd, mc, bayesian)
        if not delta:
            continue

        # ── Capa 6: Registro ──────────────────────────────────────────
        capa6.save_signal(delta)
        delta_signals.append(delta)

    # ── Capa 7 (post-loop): feedback ──────────────────────────────────
    capa7.run()

    logger.info(f"PIPELINE COMPLETE — {len(delta_signals)} señal(es) generada(s)")
    return delta_signals


def _run_from_data(markets, news):
    """Ejecuta capas 2-7 con datos ya cargados (útil para demo y tests)."""
    signals_filtered = capa2.filter_signals(markets, news)
    if not signals_filtered:
        logger.info("Sin señales relevantes.")
        return []

    weights = capa7.get_weights()
    delta_signals: List[DeltaSignal] = []

    for fs in signals_filtered:
        crowd    = capa3.simulate_crowd_reaction(fs)
        bayesian = capa3.get_bayesian_prior(fs.market.category, weights)
        mc       = capa4.run_monte_carlo(fs, crowd, bayesian)
        delta    = capa5.compute_delta_signal(fs, crowd, mc, bayesian)
        if not delta:
            continue
        capa6.save_signal(delta)
        delta_signals.append(delta)

    capa7.run()
    logger.info(f"Pipeline (demo) completo: {len(delta_signals)} señal(es)")
    return delta_signals


def print_report(signals: List[DeltaSignal]):
    if not signals:
        print("\n  Sin señales en este ciclo.\n")
        return

    print(f"\n{'═'*65}")
    print(f"  SEÑALES GENERADAS: {len(signals)}")
    print(f"{'═'*65}")

    for s in signals:
        bar = "▲" if s.delta > 0 else "▼"
        print(f"""
  [{s.signal_id}] {s.action}  {bar}
  Mercado   : {s.market.question[:70]}
  Categoría : {s.market.category}
  P_mercado : {s.p_polymarket:.3f}  ({s.p_polymarket*100:.1f}%)
  P_simulada: {s.p_simulated:.3f}  ({s.p_simulated*100:.1f}%)
  Delta     : {s.delta:+.3f}  ({s.delta*100:+.1f}pp)
  Confianza : {s.confidence:.2f}
  Narrativa : {s.crowd_signal.narrative}
  Fuente    : {s.filtered_signal.news.source} — {s.filtered_signal.news.title[:60]}
  {'─'*63}""")


if __name__ == "__main__":
    import sys
    demo_mode = "--demo" in sys.argv

    capa6.initialize()

    if demo_mode:
        import demo_data
        logger.info("Modo DEMO: usando datos de muestra (sin acceso a red)")
        signals = _run_from_data(demo_data.MARKETS, demo_data.NEWS)
    else:
        signals = run_pipeline()

    print_report(signals)
