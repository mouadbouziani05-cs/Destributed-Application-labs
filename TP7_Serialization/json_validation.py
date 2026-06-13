import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

@dataclass
class Report:
    id: int
    subject: str
    creator: str
    tags: List[str] = field(default_factory=list)
    level: str = "internal"
    _risk_score: float = field(default=0.0, repr=False)

HIDDEN_FIELDS = {"_risk_score"}

ALLOWED_LEVELS = {
    "public",
    "internal",
    "confidential",
    "secret"
}

MAX_SUBJECT_LENGTH = 200
MAX_TAGS = 20

def serialize_report(report: Report) -> str:
    data = {
        key: value
        for key, value in asdict(report).items()
        if key not in HIDDEN_FIELDS
    }

    return json.dumps(data, ensure_ascii=False)

def deserialize_report(raw_json: str) -> Report:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON: %s", e)
        raise ValueError("Invalid payload")

    if not isinstance(data, dict):
        raise ValueError("Invalid payload")

    errors = []

    for field_name in ("id", "subject", "creator"):
        if field_name not in data:
            errors.append(f"Missing field: {field_name}")

    if "id" in data and not isinstance(data["id"], int):
        errors.append("id must be integer")

    if "subject" in data:
        if not isinstance(data["subject"], str):
            errors.append("subject must be string")
        elif len(data["subject"]) > MAX_SUBJECT_LENGTH:
            errors.append("subject too long")

    if "creator" in data and not isinstance(data["creator"], str):
        errors.append("creator must be string")

    tags = data.get("tags", [])

    if not isinstance(tags, list):
        errors.append("tags must be a list")
    elif len(tags) > MAX_TAGS:
        errors.append("too many tags")

    level = data.get("level", "internal")

    if level not in ALLOWED_LEVELS:
        errors.append("level not allowed")

    if errors:
        logger.warning("Validation failed: %s", errors)
        raise ValueError("Invalid payload")

    return Report(
        id=data["id"],
        subject=data["subject"].strip(),
        creator=data["creator"].strip(),
        tags=tags,
        level=level
    )

if __name__ == "__main__":
    report = Report(
        id=1,
        subject="Distributed Systems Report",
        creator="Mouaad",
        tags=["python", "api"],
        level="confidential",
        _risk_score=8.7
    )

    json_output = serialize_report(report)
    print("Serialized JSON:")
    print(json_output)

    report2 = deserialize_report(json_output)
    print("\nDeserialized object:")
    print(report2)

    try:
        deserialize_report('{"id": "abc", "subject": 123}')
    except ValueError as e:
        print("\nRejected:", e)