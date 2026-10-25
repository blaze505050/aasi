"""
AASI Governor Constants — Default Limits, Thresholds & Safety Bounds.

All values are conservative defaults. They can be overridden per-task
via ResourceBudget, but the HARD_MAX values cannot be exceeded.
"""

# ─── Task Execution Limits ───
DEFAULT_TASK_TIMEOUT_SECONDS: int = 300       # 5 minutes default per task step
HARD_MAX_TIMEOUT_SECONDS: int = 3600          # 1 hour absolute ceiling
DEFAULT_MAX_CONCURRENT_TASKS: int = 4         # Max parallel task executions

# ─── CPU Limits ───
DEFAULT_MAX_CPU_PERCENT: float = 85.0         # Max CPU utilization before throttling
CRITICAL_CPU_PERCENT: float = 98.0            # Emergency threshold — halt new tasks

# ─── Memory Limits ───
DEFAULT_MAX_RAM_GB: float = 0.25              # Default per-task RAM budget (250 MB)
CRITICAL_RAM_AVAILABLE_GB: float = 0.2        # Below this (200 MB), refuse new allocations
MIN_FREE_RAM_FRACTION: float = 0.02           # Keep at least 2% RAM free

# ─── Disk Limits ───
DEFAULT_MAX_DISK_GB: float = 5.0              # Default per-task disk budget
CRITICAL_DISK_FREE_GB: float = 1.0            # Below this (1 GB), refuse disk-writing tasks

# ─── GPU Limits ───
DEFAULT_MAX_GPU_VRAM_GB: float = 4.0          # Default per-task GPU VRAM budget
CRITICAL_GPU_VRAM_FREE_FRACTION: float = 0.10 # Below 10% free, refuse GPU tasks

# ─── Network Limits ───
DEFAULT_REQUEST_TIMEOUT_SECONDS: float = 30.0 # HTTP request timeout
MAX_DOWNLOAD_SIZE_MB: float = 100.0           # Max file download size

# ─── Output Limits ───
MAX_STDOUT_CAPTURE_BYTES: int = 10 * 1024 * 1024  # 10 MB stdout/stderr capture
MAX_LOG_FILE_SIZE_BYTES: int = 50 * 1024 * 1024   # 50 MB per log file

# ─── Safety Governor ───
GOVERNOR_DECISION_LOG_MAX_ENTRIES: int = 10_000    # Rolling log size
KILL_SWITCH_COOLDOWN_SECONDS: float = 5.0          # Debounce for emergency halt
