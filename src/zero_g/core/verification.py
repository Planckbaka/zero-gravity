"""Verification protocol: evidence-based completion checks.

Port of OMC's verification system. Replaces naive string matching in
autopilot/ralph with formal, configurable verification checks.

Each check type runs a specific validation and produces fresh evidence
(within a configurable time window). A skill is not complete until all
required checks pass.
"""
from __future__ import annotations
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CheckType(Enum):
    BUILD = "build"
    TEST = "test"
    LINT = "lint"
    FUNCTIONALITY = "functionality"


class CheckResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class VerificationCheck:
    check_type: CheckType
    command: str
    description: str
    required: bool = True


@dataclass
class CheckEvidence:
    check_type: CheckType
    result: CheckResult
    output: str
    timestamp: float
    duration_seconds: float


@dataclass
class VerificationReport:
    checks: list[CheckEvidence] = field(default_factory=list)
    all_passed: bool = False

    def summary(self) -> str:
        lines = []
        for e in self.checks:
            status = "PASS" if e.result == CheckResult.PASS else "FAIL" if e.result == CheckResult.FAIL else "SKIP"
            lines.append(f"| {e.check_type.value:15} | {status:6} | {e.duration_seconds:.1f}s |")
        lines.append(f"| Overall | {'PASS' if self.all_passed else 'FAIL'} | |")
        return "\n".join(lines)


# Default check configurations
DEFAULT_CHECKS: list[VerificationCheck] = [
    VerificationCheck(CheckType.BUILD, "uv run python -c 'import zero_g'", "Python import check"),
    VerificationCheck(CheckType.TEST, "uv run pytest --tb=short -q", "Unit test suite"),
    VerificationCheck(CheckType.LINT, "uv run ruff check src/", "Lint check"),
]


def run_check(check: VerificationCheck, project_root: Path | None = None) -> CheckEvidence:
    """Run a single verification check and collect evidence."""
    start = time.time()
    try:
        result = subprocess.run(
            check.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_root) if project_root else None,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
    except subprocess.TimeoutExpired:
        output = "Command timed out after 120 seconds."
        passed = False
    except Exception as e:
        output = f"Error: {e}"
        passed = False

    return CheckEvidence(
        check_type=check.check_type,
        result=CheckResult.PASS if passed else CheckResult.FAIL,
        output=output,
        timestamp=time.time(),
        duration_seconds=time.time() - start,
    )


def run_verification(
    checks: list[VerificationCheck] | None = None,
    project_root: Path | None = None,
    freshness_seconds: float = 300,
) -> VerificationReport:
    """Run all verification checks and produce a report.

    Args:
        checks: Custom check list. Defaults to DEFAULT_CHECKS.
        project_root: Project root directory.
        freshness_seconds: Max age for evidence to be considered fresh.
    """
    checks = checks or DEFAULT_CHECKS
    evidences = []

    for check in checks:
        evidence = run_check(check, project_root)
        evidences.append(evidence)

    required_passed = all(
        e.result == CheckResult.PASS
        for e, c in zip(evidences, checks)
        if c.required
    )

    return VerificationReport(
        checks=evidences,
        all_passed=required_passed,
    )
