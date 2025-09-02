# Python Modules Package
# Contains additional analysis modules for the PepperAI system

__version__ = "1.0.0"
__author__ = "PepperAI Team"

# Import main classes for easy access
from .pepper_quality_analyzer import BellPepperQualityAnalyzer
from .advanced_ai_analyzer import AdvancedPepperAnalyzer

__all__ = [
    'BellPepperQualityAnalyzer',
    'AdvancedPepperAnalyzer'
]
