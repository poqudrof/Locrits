"""
Comprehensive Logging Service for Locrits
Tracks all system behavior including messages, Ollama calls, memory operations, and user interactions.
"""

import logging
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from functools import wraps


class LogLevel(Enum):
    """Log levels for different types of events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """Categories of events to log"""
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    OLLAMA_REQUEST = "ollama_request"
    OLLAMA_RESPONSE = "ollama_response"
    MEMORY_SAVE = "memory_save"
    MEMORY_RECALL = "memory_recall"
    MEMORY_SEARCH = "memory_search"
    MEMORY_DELETE = "memory_delete"
    MEMORY_EDIT = "memory_edit"
    WEBSOCKET_CONNECTION = "websocket_connection"
    API_REQUEST = "api_request"
    CONFIG_CHANGE = "config_change"
    ERROR_EVENT = "error_event"
    SYSTEM_EVENT = "system_event"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    category: str
    event_type: str
    locrit_name: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    error_details: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


class ComprehensiveLoggingService:
    """Main logging service for all Locrit activities"""

    def __init__(self, log_dir: str = "data", max_file_size: int = 50*1024*1024):
        """
        Initialize the comprehensive logging service.

        Args:
            log_dir: Base directory to store log files (data instead of logs)
            max_file_size: Maximum size of log files before rotation (bytes)
        """
        self.base_log_dir = Path(log_dir)
        self.base_log_dir.mkdir(exist_ok=True)
        self.max_file_size = max_file_size

        # Set up different loggers for different purposes
        self._setup_loggers()

        # In-memory log storage for recent events (for debugging)
        self.recent_logs: List[LogEntry] = []
        self.max_recent_logs = 1000

        # Performance tracking
        self._active_operations: Dict[str, float] = {}

        # Cache for per-Locrite loggers to avoid recreating them
        self._locrit_loggers: Dict[str, Dict[str, logging.Logger]] = {}

    def _setup_loggers(self):
        """Set up different loggers for different log types"""
        # Create logs subdirectory in data directory
        self.log_dir = self.base_log_dir / 'logs'
        self.log_dir.mkdir(exist_ok=True)

        # Main comprehensive logger (global logs)
        self.main_logger = self._create_logger(
            'locrit_comprehensive',
            self.log_dir / 'comprehensive.jsonl'
        )

        # Specialized loggers (global logs)
        self.message_logger = self._create_logger(
            'locrit_messages',
            self.log_dir / 'messages.jsonl'
        )

        self.ollama_logger = self._create_logger(
            'locrit_ollama',
            self.log_dir / 'ollama.jsonl'
        )

        self.memory_logger = self._create_logger(
            'locrit_memory',
            self.log_dir / 'memory.jsonl'
        )

        self.error_logger = self._create_logger(
            'locrit_errors',
            self.log_dir / 'errors.jsonl'
        )

    def _create_logger(self, name: str, log_file: Path) -> logging.Logger:
        """Create a logger with proper configuration"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # File handler with JSON format
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.DEBUG)

        # Simple formatter for JSON lines
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def _get_locrit_loggers(self, locrit_name: str) -> Dict[str, logging.Logger]:
        """Get or create loggers for a specific Locrit"""
        if locrit_name in self._locrit_loggers:
            return self._locrit_loggers[locrit_name]

        # Create directory for this Locrit
        locrit_dir = self.base_log_dir / 'locrits' / locrit_name
        locrit_dir.mkdir(parents=True, exist_ok=True)

        # Create loggers for this Locrit
        loggers = {
            'main': self._create_logger(f'locrit_{locrit_name}_comprehensive', locrit_dir / 'comprehensive.jsonl'),
            'messages': self._create_logger(f'locrit_{locrit_name}_messages', locrit_dir / 'messages.jsonl'),
            'ollama': self._create_logger(f'locrit_{locrit_name}_ollama', locrit_dir / 'ollama.jsonl'),
            'memory': self._create_logger(f'locrit_{locrit_name}_memory', locrit_dir / 'memory.jsonl'),
            'errors': self._create_logger(f'locrit_{locrit_name}_errors', locrit_dir / 'errors.jsonl'),
        }

        self._locrit_loggers[locrit_name] = loggers
        return loggers

    def _create_log_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        event_type: str,
        message: str = "",
        locrit_name: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error_details: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> LogEntry:
        """Create a structured log entry"""

        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            category=category.value,
            event_type=event_type,
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            message=message,
            data=data,
            duration_ms=duration_ms,
            error_details=error_details,
            correlation_id=correlation_id
        )

        # Add to recent logs
        self.recent_logs.append(entry)
        if len(self.recent_logs) > self.max_recent_logs:
            self.recent_logs.pop(0)

        return entry

    def _log_entry(self, entry: LogEntry):
        """Log an entry to appropriate loggers (GLOBAL ONLY to reduce disk usage)"""
        json_line = entry.to_json()

        # DISABLED per-Locrit logging to fix 1GB/sec disk leak
        # All logs go to global loggers only

        # Always log to global main logger
        self.main_logger.info(json_line)

        # Log to specialized global loggers based on category
        if entry.category in [LogCategory.USER_MESSAGE.value, LogCategory.ASSISTANT_MESSAGE.value]:
            self.message_logger.info(json_line)
        elif entry.category in [LogCategory.OLLAMA_REQUEST.value, LogCategory.OLLAMA_RESPONSE.value]:
            self.ollama_logger.info(json_line)
        elif entry.category.startswith('memory_'):
            self.memory_logger.info(json_line)
        elif entry.level in ['error', 'critical']:
            self.error_logger.error(json_line)

    # User Message Logging

    def log_user_message(
        self,
        content: str,
        locrit_name: str,
        session_id: str,
        user_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a user message"""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.USER_MESSAGE,
            event_type="message_received",
            message=f"User message to {locrit_name}",
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            data={
                "content": content,
                "content_length": len(content),
                "metadata": metadata or {}
            }
        )
        self._log_entry(entry)

    def log_assistant_message(
        self,
        content: str,
        locrit_name: str,
        session_id: str,
        user_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an assistant message"""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.ASSISTANT_MESSAGE,
            event_type="message_generated",
            message=f"Assistant response from {locrit_name}",
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            data={
                "content": content,
                "content_length": len(content),
                "metadata": metadata or {}
            }
        )
        self._log_entry(entry)

    # Ollama Logging

    def log_ollama_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        locrit_name: str,
        session_id: Optional[str] = None,
        stream: bool = False,
        correlation_id: Optional[str] = None
    ):
        """Log an Ollama API request"""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.OLLAMA_REQUEST,
            event_type="api_request",
            message=f"Ollama request to model {model}",
            locrit_name=locrit_name,
            session_id=session_id,
            correlation_id=correlation_id,
            data={
                "model": model,
                "message_count": len(messages),
                "stream": stream,
                "messages": messages  # Full messages for debugging
            }
        )
        self._log_entry(entry)

    def log_ollama_response(
        self,
        model: str,
        response: str,
        locrit_name: str,
        session_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        correlation_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log an Ollama API response"""
        level = LogLevel.ERROR if error else LogLevel.INFO
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.OLLAMA_RESPONSE,
            event_type="api_response",
            message=f"Ollama response from model {model}",
            locrit_name=locrit_name,
            session_id=session_id,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            error_details=error,
            data={
                "model": model,
                "response": response,
                "response_length": len(response) if response else 0,
                "success": error is None
            }
        )
        self._log_entry(entry)

    # Memory Operation Logging

    def log_memory_save(
        self,
        content: str,
        locrit_name: str,
        memory_type: str = "message",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log memory save operation"""
        level = LogLevel.ERROR if error else LogLevel.INFO
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.MEMORY_SAVE,
            event_type="memory_save",
            message=f"Memory save to {locrit_name}",
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            error_details=error,
            data={
                "memory_type": memory_type,
                "content_length": len(content) if content else 0,
                "metadata": metadata or {},
                "success": success
            }
        )
        self._log_entry(entry)

    def log_memory_recall(
        self,
        query: str,
        locrit_name: str,
        results_count: int,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        search_type: str = "conversation_history"
    ):
        """Log memory recall operation"""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.MEMORY_RECALL,
            event_type="memory_recall",
            message=f"Memory recall from {locrit_name}",
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            duration_ms=duration_ms,
            data={
                "query": query,
                "search_type": search_type,
                "results_count": results_count
            }
        )
        self._log_entry(entry)

    def log_memory_search(
        self,
        query: str,
        locrit_name: str,
        results_count: int,
        search_strategy: str = "auto",
        duration_ms: Optional[float] = None,
        user_id: Optional[str] = None
    ):
        """Log memory search operation"""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.MEMORY_SEARCH,
            event_type="memory_search",
            message=f"Memory search in {locrit_name}",
            locrit_name=locrit_name,
            user_id=user_id,
            duration_ms=duration_ms,
            data={
                "query": query,
                "search_strategy": search_strategy,
                "results_count": results_count
            }
        )
        self._log_entry(entry)

    def log_memory_edit(
        self,
        operation: str,  # edit_message, delete_message, edit_concept, etc.
        target_id: str,
        locrit_name: str,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log memory edit operations"""
        level = LogLevel.ERROR if error else LogLevel.INFO
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.MEMORY_EDIT,
            event_type=operation,
            message=f"Memory {operation} in {locrit_name}",
            locrit_name=locrit_name,
            user_id=user_id,
            error_details=error,
            data={
                "target_id": target_id,
                "success": success,
                "details": details or {}
            }
        )
        self._log_entry(entry)

    # WebSocket and API Logging

    def log_websocket_event(
        self,
        event_type: str,  # connect, disconnect, join_chat, etc.
        locrit_name: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Log WebSocket events"""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.WEBSOCKET_CONNECTION,
            event_type=event_type,
            message=f"WebSocket {event_type}",
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            data=data or {}
        )
        self._log_entry(entry)

    def log_api_request(
        self,
        endpoint: str,
        method: str,
        locrit_name: Optional[str] = None,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log API requests"""
        level = LogLevel.ERROR if error or (status_code and status_code >= 400) else LogLevel.INFO
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.API_REQUEST,
            event_type="api_request",
            message=f"{method} {endpoint}",
            locrit_name=locrit_name,
            user_id=user_id,
            duration_ms=duration_ms,
            error_details=error,
            data={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code
            }
        )
        self._log_entry(entry)

    # Error Logging

    def log_error(
        self,
        error: Exception,
        context: str,
        locrit_name: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log errors with full context"""
        entry = self._create_log_entry(
            level=LogLevel.ERROR,
            category=LogCategory.ERROR_EVENT,
            event_type="exception",
            message=f"Error in {context}: {str(error)}",
            locrit_name=locrit_name,
            session_id=session_id,
            user_id=user_id,
            error_details=str(error),
            data={
                "context": context,
                "error_type": type(error).__name__,
                "additional_data": additional_data or {}
            }
        )
        self._log_entry(entry)

    # System Events

    def log_system_event(
        self,
        event_type: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        data: Optional[Dict[str, Any]] = None
    ):
        """Log system-level events"""
        entry = self._create_log_entry(
            level=level,
            category=LogCategory.SYSTEM_EVENT,
            event_type=event_type,
            message=message,
            data=data or {}
        )
        self._log_entry(entry)

    # Performance Tracking

    def start_operation(self, operation_id: str) -> str:
        """Start tracking an operation's duration"""
        self._active_operations[operation_id] = time.time()
        return operation_id

    def end_operation(self, operation_id: str) -> Optional[float]:
        """End tracking an operation and return duration in milliseconds"""
        if operation_id in self._active_operations:
            start_time = self._active_operations.pop(operation_id)
            return (time.time() - start_time) * 1000
        return None

    # Query and Analysis

    def get_recent_logs(
        self,
        count: int = 100,
        category: Optional[LogCategory] = None,
        locrit_name: Optional[str] = None,
        level: Optional[LogLevel] = None
    ) -> List[LogEntry]:
        """Get recent log entries with optional filtering"""
        logs = self.recent_logs[-count:]

        if category:
            logs = [log for log in logs if log.category == category.value]
        if locrit_name:
            logs = [log for log in logs if log.locrit_name == locrit_name]
        if level:
            logs = [log for log in logs if log.level == level.value]

        return logs

    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        total_logs = len(self.recent_logs)
        categories = {}
        levels = {}
        locrits = {}

        for log in self.recent_logs:
            categories[log.category] = categories.get(log.category, 0) + 1
            levels[log.level] = levels.get(log.level, 0) + 1
            if log.locrit_name:
                locrits[log.locrit_name] = locrits.get(log.locrit_name, 0) + 1

        return {
            "total_logs": total_logs,
            "categories": categories,
            "levels": levels,
            "locrits": locrits,
            "active_operations": len(self._active_operations)
        }


# Decorator for automatic function logging
def log_function_call(
    service: ComprehensiveLoggingService,
    category: LogCategory,
    event_type: str = None
):
    """Decorator to automatically log function calls"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{int(time.time() * 1000)}"
            service.start_operation(operation_id)

            try:
                result = await func(*args, **kwargs)
                duration = service.end_operation(operation_id)

                # Log successful call
                entry = service._create_log_entry(
                    level=LogLevel.INFO,
                    category=category,
                    event_type=event_type or func.__name__,
                    message=f"Function {func.__name__} completed",
                    duration_ms=duration,
                    data={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                service._log_entry(entry)

                return result

            except Exception as e:
                duration = service.end_operation(operation_id)

                # Log error
                service.log_error(
                    error=e,
                    context=f"Function {func.__name__}",
                    additional_data={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                        "duration_ms": duration
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{int(time.time() * 1000)}"
            service.start_operation(operation_id)

            try:
                result = func(*args, **kwargs)
                duration = service.end_operation(operation_id)

                # Log successful call
                entry = service._create_log_entry(
                    level=LogLevel.INFO,
                    category=category,
                    event_type=event_type or func.__name__,
                    message=f"Function {func.__name__} completed",
                    duration_ms=duration,
                    data={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                service._log_entry(entry)

                return result

            except Exception as e:
                duration = service.end_operation(operation_id)

                # Log error
                service.log_error(
                    error=e,
                    context=f"Function {func.__name__}",
                    additional_data={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                        "duration_ms": duration
                    }
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Global instance with new data directory structure
comprehensive_logger = ComprehensiveLoggingService(log_dir="data")