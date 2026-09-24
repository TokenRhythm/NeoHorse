from importlib.metadata import version as _package_version
from .engine import DecisionEngine

__version__ = _package_version('neohorse-decision')
__all__ = ['DecisionEngine']
