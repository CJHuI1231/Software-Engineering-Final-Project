"""
集成模块

提供与其他模块的集成功能
"""

from .nlp_integration import NLPIntegration, store_nlp_results

__all__ = [
    "NLPIntegration",
    "store_nlp_results"
]
