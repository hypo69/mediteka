# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Fine-Tuner — Training Pipeline Scaffold
# =============================================================================
# Description:
#   Scaffold for the fine-tuning pipeline.
#   Defines the FineTuner class with pluggable training strategies:
#     - SFT  (Supervised Fine-Tuning)  — learn from correct answers
#     - DPO  (Direct Preference Optimization) — learn correct vs wrong pairs
#     - LoRA (Low-Rank Adaptation)     — parameter-efficient fine-tuning
#   Each strategy is a stub that will be implemented in future versions.
#   The class is designed to be extended without breaking the API.
#
# File: trainer.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial scaffold: FineTuner, TrainingStrategy enum, TrainingResult
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from enum import Enum
from typing import List, Optional

from .dataset_store import DatasetStore, QAPair, QAPairStatus, dataset_store

logger = logging.getLogger(__name__)


class TrainingStrategy(str, Enum):
    """Available fine-tuning strategies.

    Attributes:
        SFT:  Supervised Fine-Tuning — trains on (question, correct_answer) pairs.
        DPO:  Direct Preference Optimization — trains on
              (question, correct_answer, wrong_answer) triples.
        LORA: LoRA adapter training — parameter-efficient, low VRAM.
    """
    SFT  = "sft"
    DPO  = "dpo"
    LORA = "lora"


class TrainingResult:
    """Result returned by a training run.

    Attributes:
        success: Whether the run completed without fatal errors.
        strategy: Which strategy was used.
        pairs_used: Number of QA pairs included in training.
        message: Human-readable status or error description.
        artifacts: Paths to output files (adapter weights, logs, etc.).
    """

    def __init__(
        self,
        success: bool,
        strategy: TrainingStrategy,
        pairs_used: int,
        message: str,
        artifacts: Optional[dict] = None,
    ) -> None:
        self.success: bool = success
        self.strategy: TrainingStrategy = strategy
        self.pairs_used: int = pairs_used
        self.message: str = message
        self.artifacts: dict = artifacts or {}

    def to_dict(self) -> dict:
        return {
            "success":    self.success,
            "strategy":   self.strategy.value,
            "pairs_used": self.pairs_used,
            "message":    self.message,
            "artifacts":  self.artifacts,
        }


class FineTuner:
    """Orchestrates fine-tuning runs over the QA dataset.

    Selects approved pairs from DatasetStore and dispatches to the
    appropriate training strategy.  All strategies are currently stubs
    that log intent and return a placeholder result — they will be
    implemented in future versions.

    Args:
        store: DatasetStore instance. Defaults to the module singleton.

    Example:
        >>> tuner = FineTuner()
        >>> result = tuner.run(strategy=TrainingStrategy.DPO, model_id="hf::mistral-7b")
        >>> result.success
        True
        >>> result.message
        'DPO training scheduled (not yet implemented)'
    """

    def __init__(self, store: Optional[DatasetStore] = None) -> None:
        self._store: DatasetStore = store or dataset_store

    def run(
        self,
        strategy: TrainingStrategy = TrainingStrategy.SFT,
        model_id: str = "",
        output_dir: str = "training_output",
        max_pairs: int = 10_000,
    ) -> TrainingResult:
        """Launch a training run.

        Loads approved QA pairs and dispatches to the selected strategy.

        Args:
            strategy: Training method — sft / dpo / lora.
            model_id: Base model to fine-tune (e.g. ``hf::mistral-7b-instruct``).
            output_dir: Directory for saving adapter weights and logs.
            max_pairs: Maximum number of approved pairs to use.

        Returns:
            TrainingResult: Outcome of the run.
        """
        pairs: List[QAPair] = self._store.list(
            status=QAPairStatus.APPROVED, limit=max_pairs
        )

        if not pairs:
            return TrainingResult(
                success=False,
                strategy=strategy,
                pairs_used=0,
                message="No approved QA pairs found. Add and approve pairs first.",
            )

        logger.info(
            f"🚀 Starting {strategy.value.upper()} training: "
            f"{len(pairs)} pairs, model={model_id or '(default)'}"
        )

        if strategy == TrainingStrategy.SFT:
            return self._run_sft(pairs, model_id, output_dir)
        if strategy == TrainingStrategy.DPO:
            return self._run_dpo(pairs, model_id, output_dir)
        if strategy == TrainingStrategy.LORA:
            return self._run_lora(pairs, model_id, output_dir)

        return TrainingResult(
            success=False,
            strategy=strategy,
            pairs_used=0,
            message=f"Unknown strategy: {strategy}",
        )

    # ------------------------------------------------------------------
    # Strategy stubs — to be implemented
    # ------------------------------------------------------------------

    def _run_sft(
        self, pairs: List[QAPair], model_id: str, output_dir: str
    ) -> TrainingResult:
        """Supervised Fine-Tuning stub.

        Trains on (question → correct_answer) pairs using cross-entropy loss.
        Will use HuggingFace Trainer in the full implementation.
        """
        logger.info(f"[SFT] {len(pairs)} pairs queued for training (stub)")
        return TrainingResult(
            success=True,
            strategy=TrainingStrategy.SFT,
            pairs_used=len(pairs),
            message="SFT training scheduled (not yet implemented)",
        )

    def _run_dpo(
        self, pairs: List[QAPair], model_id: str, output_dir: str
    ) -> TrainingResult:
        """Direct Preference Optimization stub.

        Trains on (question, correct_answer, wrong_answer) triples.
        Requires answer_wrong to be non-empty.
        Will use TRL DPOTrainer in the full implementation.
        """
        dpo_pairs = [p for p in pairs if p.answer_wrong]
        logger.info(
            f"[DPO] {len(dpo_pairs)}/{len(pairs)} pairs have wrong answers (stub)"
        )
        return TrainingResult(
            success=True,
            strategy=TrainingStrategy.DPO,
            pairs_used=len(dpo_pairs),
            message="DPO training scheduled (not yet implemented)",
        )

    def _run_lora(
        self, pairs: List[QAPair], model_id: str, output_dir: str
    ) -> TrainingResult:
        """LoRA adapter training stub.

        Parameter-efficient fine-tuning via Low-Rank Adaptation.
        Requires much less VRAM than full fine-tuning.
        Will use PEFT + HuggingFace Trainer in the full implementation.
        """
        logger.info(f"[LoRA] {len(pairs)} pairs queued for LoRA training (stub)")
        return TrainingResult(
            success=True,
            strategy=TrainingStrategy.LORA,
            pairs_used=len(pairs),
            message="LoRA training scheduled (not yet implemented)",
        )
