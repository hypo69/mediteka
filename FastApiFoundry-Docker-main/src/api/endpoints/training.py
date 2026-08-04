# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Training API Endpoints — Dataset & Fine-Tuning
# =============================================================================
# Description:
#   REST API for managing QA training pairs and launching fine-tuning runs.
#   Prefix: /api/v1/training
#
#   Dataset endpoints:
#     POST   /training/pairs          — add a QA pair
#     GET    /training/pairs          — list pairs (filter by status/source)
#     GET    /training/pairs/{id}     — get single pair
#     PATCH  /training/pairs/{id}/approve  — approve pair
#     PATCH  /training/pairs/{id}/reject   — reject pair
#     DELETE /training/pairs/{id}     — delete pair
#     GET    /training/stats          — dataset statistics
#     GET    /training/export         — export approved pairs as JSON
#
#   Training endpoints:
#     POST   /training/run            — launch a fine-tuning run
#
# File: training.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial scaffold
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ...training.dataset_store import QAPairStatus, dataset_store
from ...training.trainer import FineTuner, TrainingStrategy

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Training"])
_tuner = FineTuner()


# ---------------------------------------------------------------------------
# Dataset — write
# ---------------------------------------------------------------------------

@router.post("/training/pairs")
async def add_qa_pair(request: dict) -> dict:
    """Add a new QA training pair.

    Args:
        request (dict): Fields:
            - question (str): User question.
            - answer_correct (str): Ideal answer.
            - answer_wrong (str, optional): Example of a bad answer.
            - source (str, optional): Origin tag. Default: "manual".
            - metadata (dict, optional): Extra fields.

    Returns:
        dict: ``{success, pair}``
    """
    question = request.get("question", "").strip()
    answer_correct = request.get("answer_correct", "").strip()

    if not question or not answer_correct:
        raise HTTPException(400, "question and answer_correct are required")

    pair = dataset_store.add(
        question=question,
        answer_correct=answer_correct,
        answer_wrong=request.get("answer_wrong", ""),
        source=request.get("source", "manual"),
        metadata=request.get("metadata"),
    )
    return {"success": True, "pair": pair.to_dict()}


@router.patch("/training/pairs/{pair_id}/approve")
async def approve_pair(pair_id: str) -> dict:
    """Approve a QA pair — mark it ready for training.

    Args:
        pair_id (str): UUID of the pair.

    Returns:
        dict: ``{success}``
    """
    if not dataset_store.approve(pair_id):
        raise HTTPException(404, f"Pair not found: {pair_id}")
    return {"success": True}


@router.patch("/training/pairs/{pair_id}/reject")
async def reject_pair(pair_id: str) -> dict:
    """Reject a QA pair — exclude it from training.

    Args:
        pair_id (str): UUID of the pair.

    Returns:
        dict: ``{success}``
    """
    if not dataset_store.reject(pair_id):
        raise HTTPException(404, f"Pair not found: {pair_id}")
    return {"success": True}


@router.delete("/training/pairs/{pair_id}")
async def delete_pair(pair_id: str) -> dict:
    """Permanently delete a QA pair.

    Args:
        pair_id (str): UUID of the pair.

    Returns:
        dict: ``{success}``
    """
    if not dataset_store.delete(pair_id):
        raise HTTPException(404, f"Pair not found: {pair_id}")
    return {"success": True}


# ---------------------------------------------------------------------------
# Dataset — read
# ---------------------------------------------------------------------------

@router.get("/training/pairs")
async def list_pairs(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List QA pairs with optional filtering.

    Args:
        status (str, optional): pending / approved / rejected.
        source (str, optional): Filter by source tag.
        limit (int): Max results. Default 100.
        offset (int): Skip first N. Default 0.

    Returns:
        dict: ``{success, pairs, total}``
    """
    status_enum = QAPairStatus(status) if status else None
    pairs = dataset_store.list(status=status_enum, source=source, limit=limit, offset=offset)
    return {
        "success": True,
        "pairs": [p.to_dict() for p in pairs],
        "total": len(pairs),
    }


@router.get("/training/pairs/{pair_id}")
async def get_pair(pair_id: str) -> dict:
    """Get a single QA pair by ID.

    Args:
        pair_id (str): UUID of the pair.

    Returns:
        dict: ``{success, pair}``
    """
    pair = dataset_store.get(pair_id)
    if not pair:
        raise HTTPException(404, f"Pair not found: {pair_id}")
    return {"success": True, "pair": pair.to_dict()}


@router.get("/training/stats")
async def training_stats() -> dict:
    """Return dataset statistics.

    Returns:
        dict: ``{success, stats}`` where stats has total/pending/approved/rejected.
    """
    return {"success": True, "stats": dataset_store.stats()}


@router.get("/training/export")
async def export_approved() -> dict:
    """Export all approved QA pairs as JSON.

    Returns:
        dict: ``{success, pairs, total}``
    """
    pairs = dataset_store.export_approved()
    return {"success": True, "pairs": pairs, "total": len(pairs)}


# ---------------------------------------------------------------------------
# Training run
# ---------------------------------------------------------------------------

@router.post("/training/run")
async def run_training(request: dict) -> dict:
    """Launch a fine-tuning run over approved QA pairs.

    Args:
        request (dict): Fields:
            - strategy (str): "sft" / "dpo" / "lora". Default: "sft".
            - model_id (str, optional): Base model to fine-tune.
            - output_dir (str, optional): Output directory. Default: "training_output".
            - max_pairs (int, optional): Max approved pairs to use. Default: 10000.

    Returns:
        dict: ``{success, result}``

    Example:
        >>> # POST /api/v1/training/run
        >>> # {"strategy": "dpo", "model_id": "hf::mistral-7b-instruct"}
    """
    strategy_str = request.get("strategy", "sft")
    try:
        strategy = TrainingStrategy(strategy_str)
    except ValueError:
        raise HTTPException(400, f"Unknown strategy: {strategy_str}. Use: sft, dpo, lora")

    result = _tuner.run(
        strategy=strategy,
        model_id=request.get("model_id", ""),
        output_dir=request.get("output_dir", "training_output"),
        max_pairs=int(request.get("max_pairs", 10_000)),
    )
    return {"success": result.success, "result": result.to_dict()}
