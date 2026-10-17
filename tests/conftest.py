"""
Pytest configuration for FMCG Analytics tests.
"""

import os
import sys

# Add src directory to Python path so tests can import project modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
