import json
import yaml
import jsonschema
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema" / "spec_schema.json"


def validate_spec(yaml_path: str) -> dict:
    """
    Load a spec YAML file, validate it against spec_schema.json,
    and enforce business rules JSON Schema cannot express.

    Returns the parsed spec dict on success.
    Raises ValueError with a clear message on any violation.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise ValueError(f"Spec file not found: {yaml_path}")

    with open(path) as f:
        spec = yaml.safe_load(f)

    if not isinstance(spec, dict):
        raise ValueError(f"Spec file did not parse to a dict: {yaml_path}")

    # Structural validation against JSON Schema
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=spec, schema=schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Schema validation failed: {e.message}") from e

    # Business rule: goal must be 20 words or fewer
    goal_words = len(spec["goal"].split())
    if goal_words > 20:
        raise ValueError(
            f"goal exceeds 20-word limit: {goal_words} words found. "
            f"Rewrite as one sentence under 20 words."
        )

    # Business rule: test_cases must include at least 1 passing and 1 failing
    types = [tc["type"] for tc in spec["test_cases"]]
    if "passing" not in types:
        raise ValueError(
            "test_cases must include at least 1 case with type: passing"
        )
    if "failing" not in types:
        raise ValueError(
            "test_cases must include at least 1 case with type: failing. "
            "The failing case proves the spec is testable, not just aspirational."
        )

    return spec


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python validator.py <path_to_spec.yaml>")
        sys.exit(1)

    try:
        spec = validate_spec(sys.argv[1])
        print(f"✓ Valid spec: {sys.argv[1]}")
        print(f"  goal: {spec['goal']}")
        print(f"  test_cases: {len(spec['test_cases'])} "
              f"({sum(1 for t in spec['test_cases'] if t['type'] == 'passing')} passing, "
              f"{sum(1 for t in spec['test_cases'] if t['type'] == 'failing')} failing)")
    except ValueError as e:
        print(f"✗ Invalid spec: {e}")
        sys.exit(1)
