# Maps each source PDF to its RBAC metadata, per the access table in README.md.
# The ingestion pipeline looks up a file's department/access_level here instead
# of guessing it from the folder name, so the mapping is explicit and auditable.
from dataclasses import dataclass


@dataclass(frozen=True)
class AccessEntry:
    department: str
    access_level: int


ACCESS_MAP: dict[str, AccessEntry] = {
    "hr/leave_policy.pdf": AccessEntry(department="hr", access_level=1),
    "hr/code_of_conduct.pdf": AccessEntry(department="hr", access_level=1),
    "hr/performance_review.pdf": AccessEntry(department="hr", access_level=2),
    "finance/expense_policy.pdf": AccessEntry(department="finance", access_level=1),
    "finance/travel_reimbursement.pdf": AccessEntry(department="finance", access_level=1),
    "exec/compensation_committee.pdf": AccessEntry(department="exec", access_level=3),
    "exec/strategic_plan.pdf": AccessEntry(department="exec", access_level=3),
}


def get_access_entry(relative_path: str) -> AccessEntry:
    """relative_path is e.g. 'hr/leave_policy.pdf' (posix-style, relative to docs/)."""
    try:
        return ACCESS_MAP[relative_path]
    except KeyError:
        raise ValueError(f"no access mapping defined for {relative_path!r}")
