"""
SAFLA v2.1 Omni Integration Module
===================================

This module bridges OcularPrime 2.0 dwell signals into SAFLA v2.1 Omni's
adaptive learning engine. It implements the feedback loop that allows
visual attention patterns to influence system behavior.

Key concepts:
  - Context enrichment: Dwell signals + screen state → semantic context
  - Reinforcement signals: High-dwell elements score higher in priority
  - Adaptive routing: SAFLA learns which screen regions drive user engagement
  - Meta-learning: Patterns across sessions inform system optimization
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextPriority(Enum):
    """Priority levels for context signals"""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.9
    CRITICAL = 1.0


@dataclass
class SAFLAContextPayload:
    """Standardized SAFLA context event"""
    context_type: str  # 'visual_attention', 'user_intent', 'engagement', etc.
    element_id: str
    element_text: str
    focus_duration: float
    gaze_heatmap: List[List[float]]
    element_bounds: tuple
    confidence: float
    priority: float
    semantic_label: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: str = "ocular_prime"
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self):
        d = asdict(self)
        d['priority'] = self.priority
        return d


class SAFLAFeedbackLoop:
    """
    Implements SAFLA v2.1 Omni feedback integration.
    
    Responsibilities:
      1. Score dwell signals based on duration + confidence
      2. Generate semantic labels from screen context
      3. Route signals to SAFLA endpoints (context, reward, anomaly)
      4. Track feedback acceptance and rejection
      5. Adapt thresholds based on SAFLA response
    """

    def __init__(self, safla_base_url: str = "http://localhost:5000"):
        self.base_url = safla_base_url
        
        # Endpoints
        self.context_endpoint = f"{safla_base_url}/safla/context"
        self.reward_endpoint = f"{safla_base_url}/safla/reward"
        self.anomaly_endpoint = f"{safla_base_url}/safla/anomaly"
        
        # State
        self.session_id = f"ocular_{int(time.time())}"
        self.signal_history: List[SAFLAContextPayload] = []
        self.feedback_scores: Dict[str, float] = {}  # element_id -> score
        
        # Adaptive thresholds
        self.dwell_threshold = 1.5  # seconds
        self.confidence_threshold = 0.5
        self.priority_multiplier = 1.0

    def score_dwell_signal(self, duration: float, confidence: float) -> float:
        """
        Calculate engagement score (0-1) for a dwell signal.
        
        Factors:
          - Duration: longer dwells = higher engagement
          - Confidence: gaze confidence influences interpretation
          - Adaptive multiplier: previous SAFLA feedback
        """
        # Normalize duration (0.5s = 0.3, 2.0s = 1.0)
        duration_score = min(1.0, max(0.0, (duration - 0.5) / 1.5))
        
        # Confidence weight (50-100% → 0.5-1.0)
        confidence_score = max(0.5, confidence)
        
        # Combined score with SAFLA feedback influence
        raw_score = (duration_score * 0.6) + (confidence_score * 0.4)
        final_score = raw_score * self.priority_multiplier
        
        return min(1.0, final_score)

    def classify_priority(self, score: float) -> ContextPriority:
        """Map engagement score to priority level"""
        if score >= 0.9:
            return ContextPriority.CRITICAL
        elif score >= 0.6:
            return ContextPriority.HIGH
        elif score >= 0.3:
            return ContextPriority.MEDIUM
        else:
            return ContextPriority.LOW

    def generate_semantic_label(self, element_text: str, element_type: str) -> str:
        """
        Generate semantic label for screen element.
        Helps SAFLA understand the functional meaning of attention.
        """
        # Simple heuristics; can be enhanced with NLP
        keywords_map = {
            "login": ["login", "sign in", "authenticate"],
            "submit": ["submit", "send", "post", "save"],
            "navigation": ["menu", "nav", "go to", "open"],
            "input": ["enter", "type", "fill", "input"],
            "alert": ["warning", "error", "alert", "invalid"],
            "success": ["success", "complete", "done", "ok"],
        }
        
        text_lower = (element_text + " " + element_type).lower()
        for label, keywords in keywords_map.items():
            if any(kw in text_lower for kw in keywords):
                return label
        
        return "generic_element"

    async def send_context_signal(self, payload: SAFLAContextPayload) -> bool:
        """
        Send context signal to SAFLA v2.1 Omni.
        
        Returns:
          True if accepted, False if rejected/error
        """
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.context_endpoint,
                    json=payload.to_dict(),
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        response_data = await resp.json()
                        logger.info(f"SAFLA context signal accepted: {payload.element_id}")
                        
                        # Track SAFLA feedback
                        if "feedback_score" in response_data:
                            self.feedback_scores[payload.element_id] = response_data["feedback_score"]
                        
                        return True
                    else:
                        logger.warning(f"SAFLA context rejected ({resp.status})")
                        return False
        except Exception as e:
            logger.error(f"Context signal error: {e}")
            return False

    async def send_reward_signal(
        self,
        element_id: str,
        reward_value: float,
        reason: str = "dwell_engagement"
    ) -> bool:
        """
        Send reinforcement reward to SAFLA.
        
        Used to tell SAFLA: "This element/action was valuable to the user."
        """
        try:
            import aiohttp
            payload = {
                "element_id": element_id,
                "reward": reward_value,
                "reason": reason,
                "timestamp": time.time(),
                "session_id": self.session_id
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.reward_endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"SAFLA reward signal sent: {element_id} (reward={reward_value})")
                        return True
        except Exception as e:
            logger.error(f"Reward signal error: {e}")
        return False

    async def process_dwell_for_safla(
        self,
        element_id: str,
        element_text: str,
        element_type: str,
        dwell_duration: float,
        gaze_confidence: float,
        gaze_heatmap: List[List[float]],
        element_bounds: tuple
    ) -> Optional[SAFLAContextPayload]:
        """
        End-to-end processing: dwell signal → SAFLA context + reward.
        
        Steps:
          1. Score engagement
          2. Classify priority
          3. Generate semantic label
          4. Create context payload
          5. Send to SAFLA context endpoint
          6. Send reward signal if high priority
        """
        # Score and classify
        engagement_score = self.score_dwell_signal(dwell_duration, gaze_confidence)
        priority = self.classify_priority(engagement_score)
        semantic_label = self.generate_semantic_label(element_text, element_type)

        # Create SAFLA context payload
        payload = SAFLAContextPayload(
            context_type="visual_attention",
            element_id=element_id,
            element_text=element_text,
            focus_duration=dwell_duration,
            gaze_heatmap=gaze_heatmap,
            element_bounds=element_bounds,
            confidence=gaze_confidence,
            priority=priority.value,
            semantic_label=semantic_label,
            session_id=self.session_id
        )

        # Send to SAFLA
        context_accepted = await self.send_context_signal(payload)

        # If high priority, send reward signal
        if context_accepted and priority in [ContextPriority.HIGH, ContextPriority.CRITICAL]:
            reward = engagement_score * 0.95  # Scale reward to engagement
            await self.send_reward_signal(
                element_id,
                reward_value=reward,
                reason=f"high_dwell_{priority.name}"
            )

        if context_accepted:
            self.signal_history.append(payload)

        return payload if context_accepted else None

    async def learn_from_feedback(self):
        """
        Periodically analyze SAFLA feedback and adapt thresholds.
        
        This implements meta-learning: over time, OcularPrime learns
        what types of elements SAFLA values.
        """
        if len(self.signal_history) < 10:
            return  # Insufficient data

        # Analyze feedback distribution
        avg_feedback = sum(self.feedback_scores.values()) / len(self.feedback_scores)
        
        # Adaptive multiplier: increase sensitivity if SAFLA is responding positively
        if avg_feedback > 0.7:
            self.priority_multiplier = min(1.5, self.priority_multiplier + 0.05)
            logger.info(f"Adaptive multiplier increased: {self.priority_multiplier:.2f}")
        elif avg_feedback < 0.4:
            self.priority_multiplier = max(0.5, self.priority_multiplier - 0.05)
            logger.info(f"Adaptive multiplier decreased: {self.priority_multiplier:.2f}")

    def get_session_metrics(self) -> Dict[str, Any]:
        """Export session metrics"""
        return {
            "session_id": self.session_id,
            "total_signals": len(self.signal_history),
            "avg_engagement_score": (
                sum(s.priority for s in self.signal_history) / len(self.signal_history)
                if self.signal_history else 0.0
            ),
            "adaptive_multiplier": self.priority_multiplier,
            "feedback_scores": self.feedback_scores,
        }


class OcularSAFLABridge:
    """
    High-level bridge between OcularPrime's gaze dwell detector
    and SAFLA v2.1 Omni's adaptive engine.
    """

    def __init__(self, safla_base_url: str = "http://localhost:5000"):
        self.feedback_loop = SAFLAFeedbackLoop(safla_base_url)

    async def process_dwell(
        self,
        element_id: str,
        element_text: str,
        element_type: str,
        dwell_duration: float,
        gaze_confidence: float,
        gaze_heatmap: List[List[float]],
        element_bounds: tuple
    ):
        """Process a dwell event end-to-end"""
        await self.feedback_loop.process_dwell_for_safla(
            element_id=element_id,
            element_text=element_text,
            element_type=element_type,
            dwell_duration=dwell_duration,
            gaze_confidence=gaze_confidence,
            gaze_heatmap=gaze_heatmap,
            element_bounds=element_bounds
        )

        # Periodically learn from feedback
        if len(self.feedback_loop.signal_history) % 5 == 0:
            await self.feedback_loop.learn_from_feedback()

    def get_metrics(self) -> Dict[str, Any]:
        """Export bridge metrics"""
        return self.feedback_loop.get_session_metrics()
