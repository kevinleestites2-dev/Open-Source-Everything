#!/usr/bin/env python3
"""
Agent Zero Integration — Machine Learning for Trading (ML4T)
Category : QUANT_INTELLIGENCE / TRADING_CURRICULUM
Source   : https://github.com/stefan-jansen/machine-learning-for-trading
Stars    : 18,491 | Forks: 5,227
Language : Jupyter Notebook (Python)
Size     : 683 MB (150+ executed notebooks, full data pipelines)
Book     : Machine Learning for Algorithmic Trading, 2nd Ed. (800 pages, 23 chapters)
Updated  : 2026-06-03 (active)
Absorbed : 2026-06-02

ENGINE SCORE: 9/10
Reason: 18K stars — second largest repo absorbed. This is the canonical graduate-level
        curriculum for ML-driven algorithmic trading. 150+ executed notebooks covering
        every technique OpenAgora needs: alpha factor research, RL trading agents,
        GAN synthetic data, backtesting, portfolio optimization, NLP for finance.
        Not a framework — it is a battle-tested knowledge base. The Deep RL trading
        agent (Ch.22) alone is worth the score. The 101 Formulaic Alphas library
        (Ch.24) is immediate OpenAgora ammunition. No test suite (notebooks, not
        production code) — hence 9 not 10.

What it is:
    The companion repo to "Machine Learning for Algorithmic Trading" (Stefan Jansen,
    Packt, 2nd Ed.). 23 chapters + alpha factor appendix. Every chapter has:
    - Executed Jupyter notebooks (results visible without running anything)
    - Real data pipelines (Quandl, Zipline, Alphalens, Pyfolio)
    - Production-grade implementations (not toy examples)

    This is the textbook OpenAgora needs to go from "EverOS cycle" to
    "ML-driven strategy with backtested alpha factors."

    CHAPTER MAP (23 chapters + appendix):

    PART 1 — DATA & FEATURES:
    Ch.01  ML for Trading — Overview, ML4T workflow
    Ch.02  Market & Fundamental Data — OHLCV, SEC EDGAR, Quandl
    Ch.03  Alternative Data — Sentiment, web scraping, geolocation signals
    Ch.04  Alpha Factor Research — TA-Lib, Kalman filter, wavelets, Zipline
    Ch.05  Strategy Evaluation — Backtest with trades, Pyfolio, Kelly, mean-variance opt

    PART 2 — ML MODELS:
    Ch.06  ML Process — Feature engineering pipeline, cross-validation for finance
    Ch.07  Linear Models — Ridge, Lasso, Logistic Regression for alpha signals
    Ch.08  ML4T Workflow — Vectorized backtest, Backtrader, Zipline integration
    Ch.09  Time Series Models — ARIMA, ARCH/GARCH, Vector Autoregression
    Ch.10  Bayesian ML — Bayesian regression, conjugate priors, PyMC3
    Ch.11  Decision Trees & Random Forests — Feature importance, boosting
    Ch.12  Gradient Boosting Machines — LightGBM, XGBoost, SHAP values
    Ch.13  Unsupervised Learning — PCA, clustering for regime detection

    PART 3 — NLP FOR FINANCE:
    Ch.14  Working with Text Data — NLP pipeline, SEC filings, earnings calls
    Ch.15  Topic Modeling — LDA/NMF for earnings call signal extraction
    Ch.16  Word Embeddings — Word2Vec, GloVe, financial corpus training

    PART 4 — DEEP LEARNING:
    Ch.17  Deep Learning — MLP, batch norm, dropout, PyTorch + TF2
    Ch.18  CNNs — 1D convolutions for time series, order book image models
    Ch.19  RNNs — LSTM, GRU for return prediction, sequence modeling
    Ch.20  Autoencoders — Conditional risk factor models (deep PCA)
    Ch.21  GANs — DCGAN + TimeGAN for synthetic time series generation
    Ch.22  Deep RL — Q-learning, DQN, trading_env.py, live trading agent
    Ch.23  Next Steps — Production deployment patterns

    APPENDIX — ALPHA FACTOR LIBRARY (Ch.24):
    - 00: Indicator zoo (all TA indicators catalogued)
    - 01: Sample selection (universe construction)
    - 02: Common alpha factors (momentum, value, quality, volatility)
    - 03: 101 Formulaic Alphas (WorldQuant's published alpha set — full implementation)
    - 04: Factor evaluation (IC, t-stats, turnover)
    - 05: Alphalens analysis (factor tearsheet pipeline)

    KEY FILES FOR OPENAGORA:

    22_deep_reinforcement_learning/trading_env.py (10,456 bytes):
    - Full OpenAI Gym-compatible trading environment
    - State: OHLCV + technical indicators + portfolio state
    - Actions: Long / Short / Hold (discrete or continuous)
    - Reward: Sharpe-scaled P&L or raw returns
    - Reset: random episode start within date range
    - THIS is the RL training environment OpenAgora needs.

    22_deep_reinforcement_learning/04_q_learning_for_trading.ipynb (122KB):
    - DQN with experience replay + target network
    - State encoding for financial time series
    - Epsilon-greedy exploration with decay
    - Training loop with Tensorboard logging
    - Evaluation: Sharpe, max drawdown, cumulative return vs. buy-and-hold

    24_alpha_factor_library/03_101_formulaic_alphas.ipynb (5.2MB — fully executed):
    - All 101 WorldQuant alphas implemented in pandas/numpy
    - Alpha 1: rank(ts_argmax(signedpower(where(returns < 0, stddev(returns, 20), close), 2), 5)) - 0.5
    - Each alpha: formula, implementation, IC analysis
    - Ready to plug into OpenAgora's signal layer

    24_alpha_factor_library/02_common_alpha_factors.ipynb (4.1MB):
    - Momentum (1M, 3M, 6M, 12M), value (P/B, P/E), quality (ROE, ROA)
    - Volatility factors, liquidity factors
    - All with Alphalens tearsheets showing forward return IC

    05_strategy_evaluation/05_kelly_rule.ipynb:
    - Full Kelly Criterion implementation
    - Fractional Kelly for risk management
    - THIS is OpenAgora's position sizing formula.

    21_gans_for_synthetic_time_series/02_TimeGAN_TF2.ipynb:
    - TimeGAN: trains on real OHLCV → generates synthetic price series
    - Evaluation: discriminative + predictive score vs. real data
    - USE CASE: Generate synthetic Kalshi/Polymarket price histories
      for backtesting OpenAgora strategies without burning real capital.

    12_gradient_boosting_machines/ (LightGBM for alpha):
    - Train LightGBM on alpha factors → predict next-period returns
    - SHAP values for factor attribution
    - THIS is OpenAgora's ML signal layer.

    WHY 9/10 AND NOT 10/10:
    - Notebooks, not a deployable library (no pip install)
    - No tests (Jupyter-native, not pytest)
    - Data pipelines require Quandl/Zipline setup (non-trivial)
    - BUT: Zipline-reloaded is pip-installable. Alphalens is pip-installable.
      The CODE is production-grade even if the packaging isn't.

PANTHEON INTEGRATION:

    OPENAGORA (PRIMARY):
    - trading_env.py → drop into OpenAgora as the RL training env
    - 101 Formulaic Alphas → OpenAgora signal layer (replace heuristic EverOS logic)
    - Kelly Criterion → OpenAgora position sizing (replaces fixed lot sizing)
    - LightGBM alpha pipeline → OpenAgora ML signal generator
    - TimeGAN → synthetic data for backtesting without live capital risk

    ZEUSPRIME:
    - Alpha factors → identify momentum signals on Polymarket prediction markets
    - GBM model → predict market resolution probability from historical patterns
    - Kelly → position sizing on Kalshi/Polymarket bets

    SCOUTPRIME:
    - NLP pipeline (Ch.14) → extract sentiment signals from property news, zoning changes
    - Topic modeling (Ch.15) → cluster real estate market narratives
    - Factor evaluation (Alphalens) → score property data sources by predictive IC

    FLUXPRIME:
    - ML4T workflow as the intelligence layer for capital allocation decisions
    - SAFLA feedback loop maps to the ML4T backtest → retrain → redeploy cycle
    - Regime detection (Ch.13 clustering) → FluxPrime PIVOT/CONTINUE decision

    MIDAS PRIME:
    - Strategy evaluation (Pyfolio) → War Chest performance tearsheet
    - Sharpe, max drawdown, rolling beta → MidasPrime liquidity strike triggers
"""

import os
import sys
import json
import urllib.request
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List


# ─── CONFIG ──────────────────────────────────────────────────────────────────

GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "GH_TOKEN_INJECTED_AT_RUNTIME")
SLUG           = "stefan-jansen/machine-learning-for-trading"
REPO_URL       = f"https://github.com/{SLUG}"
BOOK_URL       = "https://www.amazon.com/Machine-Learning-Algorithmic-Trading-alternative/dp/1839217715"
COMMUNITY_URL  = "https://exchange.ml4trading.io/"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")


# ─── GITHUB FETCH ────────────────────────────────────────────────────────────

def _gh_get(path: str) -> Any:
    url = f"https://api.github.com/repos/{SLUG}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            if isinstance(data, dict) and "content" in data:
                return base64.b64decode(data["content"]).decode(errors="replace")
            return data
    except Exception as e:
        return {"error": str(e)}


# ─── CHAPTER REGISTRY ────────────────────────────────────────────────────────

CHAPTERS = {
    "01": {"name": "ML for Trading",                "pantheon": "Overview, ML4T workflow — FluxPrime intelligence layer"},
    "02": {"name": "Market & Fundamental Data",     "pantheon": "OHLCV + SEC EDGAR pipelines — OpenAgora data ingestion"},
    "03": {"name": "Alternative Data",              "pantheon": "Sentiment + web scraping — ScoutPrime signal sources"},
    "04": {"name": "Alpha Factor Research",         "pantheon": "TA-Lib + Kalman + Zipline — OpenAgora alpha generation"},
    "05": {"name": "Strategy Evaluation",           "pantheon": "Backtest + Pyfolio + Kelly — OpenAgora risk management"},
    "06": {"name": "ML Process",                    "pantheon": "Feature pipeline + CV — OpenAgora model training"},
    "07": {"name": "Linear Models",                 "pantheon": "Ridge/Lasso/Logistic — OpenAgora baseline signal model"},
    "08": {"name": "ML4T Workflow",                 "pantheon": "Backtrader + Zipline — OpenAgora full backtest pipeline"},
    "09": {"name": "Time Series Models",            "pantheon": "ARIMA + GARCH — OpenAgora volatility regime detection"},
    "10": {"name": "Bayesian ML",                   "pantheon": "Bayesian regression — ZeusPrime probability calibration"},
    "11": {"name": "Decision Trees + RF",           "pantheon": "Feature importance — OpenAgora signal selection"},
    "12": {"name": "Gradient Boosting (LightGBM)",  "pantheon": "LightGBM + SHAP — OpenAgora primary ML signal layer"},
    "13": {"name": "Unsupervised Learning",         "pantheon": "PCA + clustering — FluxPrime market regime detection"},
    "14": {"name": "Text Data (NLP)",               "pantheon": "SEC filings + earnings — ScoutPrime property news NLP"},
    "15": {"name": "Topic Modeling",                "pantheon": "LDA/NMF — ScoutPrime market narrative clustering"},
    "16": {"name": "Word Embeddings",               "pantheon": "Word2Vec/GloVe — ContentPrime financial corpus"},
    "17": {"name": "Deep Learning",                 "pantheon": "MLP + PyTorch/TF2 — OpenAgora neural signal models"},
    "18": {"name": "CNNs",                          "pantheon": "1D conv time series — OpenAgora order book patterns"},
    "19": {"name": "RNNs (LSTM/GRU)",               "pantheon": "Sequence modeling — OpenAgora return prediction"},
    "20": {"name": "Autoencoders",                  "pantheon": "Conditional risk factors — OpenAgora factor model"},
    "21": {"name": "GANs (TimeGAN)",                "pantheon": "Synthetic price series — ZeusPrime backtesting data"},
    "22": {"name": "Deep Reinforcement Learning",   "pantheon": "trading_env.py + DQN — OpenAgora RL trading agent"},
    "23": {"name": "Next Steps",                    "pantheon": "Production deployment — Pantheon Prime deploy patterns"},
    "24": {"name": "Alpha Factor Library",          "pantheon": "101 Formulaic Alphas + Alphalens — OpenAgora signal arsenal"},
}

# ─── PRIORITY TARGETS FOR OPENAGORA ─────────────────────────────────────────

OPENAGORA_PRIORITY = {
    "trading_env": {
        "file":    "22_deep_reinforcement_learning/trading_env.py",
        "size":    "10,456 bytes",
        "what":    "Full OpenAI Gym-compatible trading environment",
        "state":   "OHLCV + technical indicators + portfolio state",
        "actions": "Long / Short / Hold (discrete or continuous)",
        "reward":  "Sharpe-scaled P&L or raw returns",
        "use":     "Drop into OpenAgora as RL training env. Replace EverOS heuristic loop.",
    },
    "dqn_trading": {
        "file":    "22_deep_reinforcement_learning/04_q_learning_for_trading.ipynb",
        "size":    "122KB executed",
        "what":    "DQN with experience replay + target network for trading",
        "eval":    "Sharpe, max drawdown, cumulative return vs. buy-and-hold",
        "use":     "Train OpenAgora's RL brain on Kalshi/Polymarket historical data",
    },
    "101_alphas": {
        "file":    "24_alpha_factor_library/03_101_formulaic_alphas.ipynb",
        "size":    "5.2MB fully executed",
        "what":    "All 101 WorldQuant formulaic alphas implemented in pandas/numpy",
        "use":     "OpenAgora signal layer. Replace heuristic price signals with tested alphas.",
        "immediate": True,
    },
    "common_alphas": {
        "file":    "24_alpha_factor_library/02_common_alpha_factors.ipynb",
        "size":    "4.1MB fully executed",
        "what":    "Momentum, value, quality, volatility, liquidity factors with IC tearsheets",
        "use":     "OpenAgora alpha factor baseline. Start here before the 101.",
        "immediate": True,
    },
    "kelly": {
        "file":    "05_strategy_evaluation/05_kelly_rule.ipynb",
        "what":    "Full Kelly Criterion + Fractional Kelly implementation",
        "use":     "OpenAgora position sizing. Replace fixed lot sizing with Kelly-optimal.",
        "immediate": True,
    },
    "lightgbm_alpha": {
        "file":    "12_gradient_boosting_machines/",
        "what":    "LightGBM trained on alpha factors → predict next-period returns + SHAP",
        "use":     "OpenAgora ML signal generator. Outperforms linear models on finance data.",
    },
    "timegan": {
        "file":    "21_gans_for_synthetic_time_series/02_TimeGAN_TF2.ipynb",
        "what":    "TimeGAN: train on real OHLCV → generate synthetic price histories",
        "use":     "ZeusPrime / OpenAgora backtesting without burning live capital. Generate 10,000 synthetic Polymarket histories.",
    },
    "pyfolio": {
        "file":    "05_strategy_evaluation/03_pyfolio_demo.ipynb",
        "what":    "Sharpe, max drawdown, rolling beta, factor exposure tearsheet",
        "use":     "MidasPrime War Chest performance reporting. Liquidity strike trigger metrics.",
    },
    "garch": {
        "file":    "09_time_series_models/",
        "what":    "ARCH/GARCH volatility models",
        "use":     "OpenAgora circuit breaker: pause trading when GARCH vol > threshold.",
    },
}

# ─── ZEUS PRIME APPLICATIONS ─────────────────────────────────────────────────

ZEUS_APPLICATIONS = {
    "polymarket_alpha": "101 Formulaic Alphas adapted to prediction market resolution patterns",
    "kelly_betting":    "Kelly Criterion for Polymarket position sizing (already in TOOLS.md)",
    "bayesian_prob":    "Ch.10 Bayesian calibration of market resolution probabilities",
    "synthetic_data":   "TimeGAN synthetic Polymarket price histories for backtesting",
}

# ─── INSTALL STACK ───────────────────────────────────────────────────────────

INSTALL = {
    "core": [
        "pip install zipline-reloaded",
        "pip install alphalens-reloaded",
        "pip install pyfolio-reloaded",
        "pip install lightgbm xgboost",
        "pip install ta-lib",
        "pip install gymnasium",   # for trading_env.py
        "pip install torch torchvision",
        "pip install tensorflow",  # for TimeGAN
    ],
    "data": [
        "# Quandl data (free tier available):",
        "pip install quandl",
        "quandl.ApiConfig.api_key = 'YOUR_KEY'",
        "# Or use yfinance (free, no key):",
        "pip install yfinance",
    ],
    "quick_start": [
        "# Clone and run trading_env.py immediately:",
        "git clone https://github.com/stefan-jansen/machine-learning-for-trading",
        "cd machine-learning-for-trading/22_deep_reinforcement_learning",
        "pip install gymnasium lightgbm",
        "python trading_env.py  # runs standalone test",
    ],
    "termux_note": "LightGBM + yfinance + gymnasium are Termux-installable. PyTorch ARM builds available. TF2 requires Nexus.",
}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class ML4TConnector:
    """
    Pantheon connector for Machine Learning for Trading (ML4T).
    18,491 stars. 5,227 forks. 150+ executed notebooks. 800-page book companion.

    Pantheon Role: QUANT_INTELLIGENCE / TRADING_CURRICULUM

    This is OpenAgora's brain. The 101 Formulaic Alphas, Kelly Criterion,
    LightGBM signal pipeline, TimeGAN synthetic data, and DQN trading agent
    are the upgrade path from EverOS heuristics to production ML trading.

    Usage:
        ml = ML4TConnector()
        print(ml.health_check())
        print(ml.openagora_roadmap())
        print(ml.chapter_info("22"))
        print(ml.priority_target("trading_env"))
        print(ml.zeus_applications())
        print(ml.install_stack())
    """

    REPO_URL      = REPO_URL
    CATEGORY      = "QUANT_INTELLIGENCE"
    ROLE          = "TRADING_CURRICULUM"
    PANTHEON_ROLE = "QUANT_INTELLIGENCE / TRADING_CURRICULUM"
    SCORE         = 9
    STARS         = 18491
    FORKS         = 5227
    NOTEBOOKS     = 150
    CHAPTERS      = 23

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        return {
            "name":         "ml4t",
            "category":     self.CATEGORY,
            "role":         self.PANTHEON_ROLE,
            "score":        self.SCORE,
            "score_note":   "18K stars. Canonical ML-trading curriculum. 150+ executed notebooks. 101 Formulaic Alphas + Kelly + DQN trading agent = OpenAgora upgrade path.",
            "stars":        self.STARS,
            "forks":        self.FORKS,
            "notebooks":    self.NOTEBOOKS,
            "chapters":     self.CHAPTERS,
            "size_mb":      683,
            "book":         BOOK_URL,
            "community":    COMMUNITY_URL,
            "key_capabilities": [
                "101 WorldQuant Formulaic Alphas — full pandas/numpy implementation (immediate OpenAgora signal layer)",
                "Kelly Criterion + Fractional Kelly — OpenAgora position sizing formula",
                "DQN trading agent + OpenAI Gym trading_env.py — RL brain for OpenAgora",
                "LightGBM + SHAP alpha pipeline — ML signal generator (outperforms linear on finance)",
                "TimeGAN synthetic time series — backtest without burning live capital",
                "Pyfolio tearsheet — MidasPrime War Chest performance reporting",
                "GARCH volatility models — OpenAgora circuit breaker trigger",
                "NLP pipeline (SEC filings, earnings calls) — ScoutPrime financial text signals",
                "Full backtest stack: Zipline + Backtrader + Alphalens + Pyfolio",
                "Regime detection (PCA + clustering) — FluxPrime PIVOT/CONTINUE intelligence",
            ],
            "pantheon_primes": {
                "OpenAgora":  "PRIMARY — alpha factors, Kelly, LightGBM, DQN, TimeGAN, GARCH",
                "ZeusPrime":  "Polymarket alpha + Kelly betting + Bayesian calibration + TimeGAN",
                "ScoutPrime": "NLP pipeline + topic modeling for real estate market signals",
                "FluxPrime":  "Regime detection + ML4T workflow as intelligence layer",
                "MidasPrime": "Pyfolio War Chest reporting + Sharpe-based strike triggers",
            },
            "repo":   self.REPO_URL,
            "status": "reference — clone and extract, not a pip package",
        }

    # ── OPENAGORA ROADMAP ─────────────────────────────────────────────────────

    def openagora_roadmap(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "openagora_roadmap",
            "phase_1_immediate": {
                "title": "Replace EverOS Heuristics with Tested Alphas",
                "steps": [
                    "1. Clone ml4t repo",
                    "2. Run 24_alpha_factor_library/02_common_alpha_factors.ipynb",
                    "3. Extract momentum (12M), volatility, and quality factors",
                    "4. Wire as signal layer in OpenAgora agora_engine.py",
                    "5. Replace current price heuristics with IC-validated alpha signals",
                ],
                "time": "1-2 days",
            },
            "phase_2_kelly": {
                "title": "Kelly Criterion Position Sizing",
                "steps": [
                    "1. Run 05_strategy_evaluation/05_kelly_rule.ipynb",
                    "2. Extract fractional_kelly(win_prob, win_loss_ratio, fraction=0.5) function",
                    "3. Wire into OpenAgora's position sizing layer",
                    "4. Set fraction=0.25 (quarter-Kelly) for safety during initial deployment",
                ],
                "time": "4 hours",
            },
            "phase_3_lightgbm": {
                "title": "LightGBM ML Signal Layer",
                "steps": [
                    "1. Run 12_gradient_boosting_machines/ notebooks",
                    "2. Train LightGBM on alpha factors → predict next-period return sign",
                    "3. Use SHAP to identify top-3 signal drivers for OpenAgora",
                    "4. Replace heuristic signal layer with LightGBM predictions",
                ],
                "time": "3-5 days (data collection + training)",
            },
            "phase_4_rl": {
                "title": "RL Trading Agent (OpenAgora's Brain)",
                "steps": [
                    "1. Copy trading_env.py → OpenAgora/envs/",
                    "2. Run 22_deep_reinforcement_learning/04_q_learning_for_trading.ipynb",
                    "3. Train DQN on historical Polymarket/Kalshi data",
                    "4. Replace EverOS decision loop with trained RL policy",
                ],
                "time": "1-2 weeks (training time depends on Nexus GPU)",
            },
            "phase_5_synthetic": {
                "title": "TimeGAN Synthetic Data for Safe Backtesting",
                "steps": [
                    "1. Run 21_gans_for_synthetic_time_series/02_TimeGAN_TF2.ipynb",
                    "2. Train on real Polymarket price history",
                    "3. Generate 10,000 synthetic scenarios",
                    "4. Backtest all strategy variants on synthetic data before live deploy",
                ],
                "time": "1 week (GPU required for TimeGAN training)",
            },
        })

    # ── CHAPTERS ──────────────────────────────────────────────────────────────

    def chapter_info(self, ch: str) -> Dict:
        info = CHAPTERS.get(ch.zfill(2))
        if not info:
            return {"error": f"Unknown chapter: {ch}. Available: {list(CHAPTERS.keys())}"}
        return self.to_pantheon_signal({
            "action":  "chapter_info",
            "chapter": ch,
            "info":    info,
        })

    def chapter_map(self) -> Dict:
        return self.to_pantheon_signal({
            "action":   "chapter_map",
            "chapters": CHAPTERS,
            "total":    len(CHAPTERS),
        })

    # ── PRIORITY TARGETS ──────────────────────────────────────────────────────

    def priority_target(self, name: str) -> Dict:
        target = OPENAGORA_PRIORITY.get(name)
        if not target:
            return {"error": f"Unknown target: {name}. Available: {list(OPENAGORA_PRIORITY.keys())}"}
        return self.to_pantheon_signal({
            "action": "priority_target",
            "name":   name,
            "config": target,
        })

    def all_priority_targets(self) -> Dict:
        return self.to_pantheon_signal({
            "action":    "all_priority_targets",
            "immediate": {k: v for k, v in OPENAGORA_PRIORITY.items() if v.get("immediate")},
            "all":       OPENAGORA_PRIORITY,
        })

    # ── ZEUS APPLICATIONS ─────────────────────────────────────────────────────

    def zeus_applications(self) -> Dict:
        return self.to_pantheon_signal({
            "action":       "zeus_applications",
            "applications": ZEUS_APPLICATIONS,
            "priority":     "kelly_betting — implement first. Polymarket already wired in TOOLS.md.",
        })

    # ── TRADING ENV ───────────────────────────────────────────────────────────

    def trading_env_source(self) -> Dict:
        content = _gh_get("22_deep_reinforcement_learning/trading_env.py")
        return self.to_pantheon_signal({
            "action":  "trading_env_source",
            "file":    "22_deep_reinforcement_learning/trading_env.py",
            "content": content[:4000] if isinstance(content, str) else str(content),
            "note":    "Full OpenAI Gym trading env. Drop into OpenAgora/envs/trading_env.py. Wire to historical Kalshi data.",
        })

    # ── INSTALL ───────────────────────────────────────────────────────────────

    def install_stack(self) -> Dict:
        return self.to_pantheon_signal({
            "action":  "install_stack",
            "install": INSTALL,
        })

    # ── SIGNAL ────────────────────────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "ml4t",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[ML4T] {message}", "parse_mode": "Markdown"}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[ML4T] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ml = ML4TConnector()

    if len(sys.argv) < 2:
        print(json.dumps(ml.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(ml.health_check(), indent=2))
    elif cmd == "roadmap":
        print(json.dumps(ml.openagora_roadmap(), indent=2))
    elif cmd == "chapters":
        print(json.dumps(ml.chapter_map(), indent=2))
    elif cmd == "chapter" and len(sys.argv) > 2:
        print(json.dumps(ml.chapter_info(sys.argv[2]), indent=2))
    elif cmd == "targets":
        print(json.dumps(ml.all_priority_targets(), indent=2))
    elif cmd == "target" and len(sys.argv) > 2:
        print(json.dumps(ml.priority_target(sys.argv[2]), indent=2))
    elif cmd == "zeus":
        print(json.dumps(ml.zeus_applications(), indent=2))
    elif cmd == "env":
        print(json.dumps(ml.trading_env_source(), indent=2))
    elif cmd == "install":
        print(json.dumps(ml.install_stack(), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|roadmap|chapters|chapter <n>|targets|target <name>|zeus|env|install]")
