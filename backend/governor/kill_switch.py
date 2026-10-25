"""
AASI 2.0 Kill Switch — Emergency Halt & Cooperative Cancellation Mechanism.

Provides atomic, thread-safe, and async-safe emergency halting for all
agent and solver processes across the system.
"""

from __future__ import annotations

import time
import logging
import threading
import asyncio
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.governor.constants import KILL_SWITCH_COOLDOWN_SECONDS

logger = logging.getLogger("aasi.governor.kill_switch")


class KillSwitchState(BaseModel):
    """Observable state of the global emergency kill switch."""
    is_tripped: bool = False
    tripped_at: Optional[float] = None
    tripped_by: Optional[str] = None
    reason: Optional[str] = None
    trip_count: int = 0


class KillSwitchActiveError(RuntimeError):
    """Raised when an operation is attempted while the emergency halt is active."""
    pass


class KillSwitch:
    """
    Global emergency kill switch singleton.
    Provides synchronous and asynchronous cancellation hooks.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._is_tripped = False
        self._tripped_at: Optional[float] = None
        self._tripped_by: Optional[str] = None
        self._reason: Optional[str] = None
        self._trip_count: int = 0
        self._last_reset_time: float = 0.0

        # Synchronization events
        self._thread_event = threading.Event()
        self._thread_event.set()  # Set means "RUNNING", cleared means "HALTED"
        self._async_event: Optional[asyncio.Event] = None

    def _get_async_event(self) -> asyncio.Event:
        if self._async_event is None:
            self._async_event = asyncio.Event()
            self._async_event.set()
        return self._async_event

    @property
    def is_tripped(self) -> bool:
        with self._lock:
            return self._is_tripped

    def get_state(self) -> KillSwitchState:
        with self._lock:
            return KillSwitchState(
                is_tripped=self._is_tripped,
                tripped_at=self._tripped_at,
                tripped_by=self._tripped_by,
                reason=self._reason,
                trip_count=self._trip_count,
            )

    def trip(self, reason: str, triggered_by: str = "operator") -> KillSwitchState:
        """
        Engages the emergency halt immediately. Fail-closed.
        All executing agents, solvers, and background tasks are notified.
        """
        with self._lock:
            self._is_tripped = True
            self._tripped_at = time.time()
            self._tripped_by = triggered_by
            self._reason = reason
            self._trip_count += 1
            self._thread_event.clear()

            if self._async_event is not None:
                self._async_event.clear()

            logger.critical(
                "🚨 EMERGENCY KILL SWITCH ENGAGED by %s: %s (trip #%d)",
                triggered_by, reason, self._trip_count
            )

            return KillSwitchState(
                is_tripped=self._is_tripped,
                tripped_at=self._tripped_at,
                tripped_by=self._tripped_by,
                reason=self._reason,
                trip_count=self._trip_count,
            )

    def reset(self, authorized_by: str = "operator", force: bool = False) -> KillSwitchState:
        """
        Disengages emergency halt after mandatory cooldown debounce (or forced).
        """
        with self._lock:
            now = time.time()
            if not force and self._tripped_at and (now - self._tripped_at) < KILL_SWITCH_COOLDOWN_SECONDS:
                remaining = round(KILL_SWITCH_COOLDOWN_SECONDS - (now - self._tripped_at), 1)
                raise ValueError(
                    f"Kill switch cannot be reset yet. Cooldown debounce active ({remaining}s remaining)"
                )

            self._is_tripped = False
            self._tripped_at = None
            self._tripped_by = None
            self._reason = None
            self._last_reset_time = now
            self._thread_event.set()

            if self._async_event is not None:
                self._async_event.set()

            logger.info("🟢 EMERGENCY KILL SWITCH RESET by %s", authorized_by)

            return KillSwitchState(
                is_tripped=self._is_tripped,
                tripped_at=None,
                tripped_by=None,
                reason=None,
                trip_count=self._trip_count,
            )

    def check_or_raise(self) -> None:
        """
        Fast inline assertion. If kill switch is active, raises KillSwitchActiveError.
        """
        with self._lock:
            if self._is_tripped:
                raise KillSwitchActiveError(
                    f"EMERGENCY HALT ACTIVE (tripped by {self._tripped_by}: {self._reason})"
                )

    def is_running(self) -> bool:
        """Cooperative polling check for workers."""
        return not self.is_tripped


# Global singleton
global_kill_switch = KillSwitch()
