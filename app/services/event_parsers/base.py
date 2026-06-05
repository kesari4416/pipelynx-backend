"""
Base parser interface for CI/CD event normalization.
All platform-specific parsers must inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseEventParser(ABC):
    """Abstract base class for CI/CD event parsers"""
    
    source: str = "unknown"  # Override in subclasses
    
    @abstractmethod
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        """Determine if this parser can handle the given event"""
        pass
    
    @abstractmethod
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse the event payload into a normalized PipelineRun dict.
        Returns None if event should be ignored (e.g., not a pipeline event).
        """
        pass
    
    @staticmethod
    def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
        """Helper: Parse ISO 8601 datetime strings safely"""
        if not value:
            return None
        try:
            # Handle 'Z' suffix and various ISO formats
            cleaned = value.replace('Z', '+00:00') if isinstance(value, str) else value
            return datetime.fromisoformat(cleaned)
        except (ValueError, AttributeError, TypeError):
            return None
    
    @staticmethod
    def calculate_duration(started_at: Optional[datetime], completed_at: Optional[datetime]) -> Optional[float]:
        """Helper: Calculate duration in seconds"""
        if started_at and completed_at:
            return (completed_at - started_at).total_seconds()
        return None
