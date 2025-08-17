"""
Agentic Fact-Check System Package

This package contains all the components for the fact-checking system.
"""

__version__ = "1.0.0"
__author__ = "Agentic Fact-Check Team"

# Import main classes for easy access
from .config import Config
from .fact_checking_agent import FactCheckingAgent
from .models import ContentItem, Claim, VerificationResult

__all__ = [
    'Config',
    'FactCheckingAgent', 
    'ContentItem',
    'Claim',
    'VerificationResult'
]
