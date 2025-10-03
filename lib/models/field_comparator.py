"""Field-by-field comparison with intelligent matching for array fields."""

from typing import Any, Dict, List, Literal, Optional, Tuple
from difflib import SequenceMatcher

from pydantic import BaseModel, Field


class ComparisonExample(BaseModel):
    """Example of a specific mismatch for debugging."""

    instance_identifier: str
    expected_value: Optional[str] = None  # Serialized as string for compatibility
    actual_value: Optional[str] = None  # Serialized as string for compatibility
    matched: bool
    note: Optional[str] = None


class FieldComparison(BaseModel):
    """Single field comparison result with full diagnostic info."""

    field_path: str
    comparison_type: Literal["strict", "llm"]
    total_instances: int
    passed_instances: int
    failed_instances: int
    passed: bool
    rationale: str
    examples: List[ComparisonExample] = Field(default_factory=list)
    matching_strategy: Optional[str] = None


class FieldComparator:
    """Handles field-by-field comparison with multiple matching strategies."""

    # Configuration constants
    MAX_EXAMPLES = 5
    FUZZY_THRESHOLD = 0.6
    GOOD_MATCH_THRESHOLD = 0.8
    TRUNCATE_LENGTH = 30

    def __init__(self, field_config: dict | set, ignore_config: dict | set = None):
        self.field_config = field_config
        self.ignore_config = ignore_config or set()

    def compare_fields(
        self,
        expected: BaseModel,
        result: BaseModel,
        comparison_type: Literal["strict", "llm"] = "strict",
    ) -> List[FieldComparison]:
        """Compare all configured fields and return detailed results."""
        comparisons = []

        if isinstance(self.field_config, set):
            # Top-level scalar fields
            for field_name in self.field_config:
                comparison = self._compare_scalar_field(
                    expected, result, field_name, comparison_type
                )
                comparisons.append(comparison)

        elif isinstance(self.field_config, dict):
            # Nested fields (arrays/objects)
            for parent_field, child_config in self.field_config.items():
                if isinstance(child_config, dict) and "__all__" in child_config:
                    # Array with field specs
                    array_comparisons = self._compare_array_fields(
                        expected,
                        result,
                        parent_field,
                        child_config["__all__"],
                        comparison_type,
                    )
                    comparisons.extend(array_comparisons)
                elif isinstance(child_config, list):
                    # Direct list of fields
                    array_comparisons = self._compare_array_fields(
                        expected, result, parent_field, child_config, comparison_type
                    )
                    comparisons.extend(array_comparisons)

        return comparisons

    def _compare_scalar_field(
        self,
        expected: BaseModel,
        result: BaseModel,
        field_name: str,
        comparison_type: str,
    ) -> FieldComparison:
        """Compare a single scalar field."""
        exp_val = getattr(expected, field_name, None)
        res_val = getattr(result, field_name, None)

        matched = self._values_match(exp_val, res_val)

        examples = []
        if not matched:
            examples.append(
                ComparisonExample(
                    instance_identifier=field_name,
                    expected_value=self._serialize_value(exp_val),
                    actual_value=self._serialize_value(res_val),
                    matched=False,
                    note="Direct field comparison",
                )
            )

        return FieldComparison(
            field_path=field_name,
            comparison_type=comparison_type,
            total_instances=1,
            passed_instances=1 if matched else 0,
            failed_instances=0 if matched else 1,
            passed=matched,
            rationale=self._build_rationale(
                field_name, matched, 1, 1 if matched else 0
            ),
            examples=examples,
        )

    def _compare_array_fields(
        self,
        expected: BaseModel,
        result: BaseModel,
        array_field: str,
        field_names: List[str],
        comparison_type: str,
    ) -> List[FieldComparison]:
        """Compare fields across array items with intelligent matching."""
        exp_array = getattr(expected, array_field, [])
        res_array = getattr(result, array_field, [])

        # Convert to dicts if needed
        exp_items = [self._to_dict(item) for item in exp_array]
        res_items = [self._to_dict(item) for item in res_array]

        # Try multiple matching strategies
        matches, strategy = self._match_array_items(exp_items, res_items, field_names)

        # Compare each field across matched items
        comparisons = []
        for field_name in field_names:
            comparison = self._compare_field_across_matches(
                matches, field_name, array_field, comparison_type, strategy
            )
            comparisons.append(comparison)

        return comparisons

    def _match_array_items(
        self,
        expected_items: List[Dict],
        result_items: List[Dict],
        field_names: List[str],
    ) -> Tuple[List[Tuple[Optional[Dict], Optional[Dict], str]], str]:
        """Match array items using multiple strategies."""
        if len(expected_items) == 0 and len(result_items) == 0:
            return [], "empty"

        # Strategy 1: Match by first field (usually 'text' or similar)
        if field_names:
            primary_field = field_names[0]
            matches = self._match_by_field(expected_items, result_items, primary_field)
            if self._is_good_match(matches):
                return matches, f"by_{primary_field}"

        # Strategy 2: Match by index (if counts match)
        if len(expected_items) == len(result_items):
            matches = [
                (exp, res, f"index_{i}")
                for i, (exp, res) in enumerate(zip(expected_items, result_items))
            ]
            return matches, "by_index"

        # Strategy 3: Best effort with fuzzy matching
        matches = self._match_best_effort(expected_items, result_items, field_names)
        return matches, "best_effort"

    def _match_by_field(
        self, expected_items: List[Dict], result_items: List[Dict], match_field: str
    ) -> List[Tuple[Optional[Dict], Optional[Dict], str]]:
        """Match items by a specific field value."""
        matches = []
        result_copy = list(result_items)

        for i, exp_item in enumerate(expected_items):
            exp_val = exp_item.get(match_field)
            matched_item = None
            match_id = f"exp[{i}]"

            # Find matching result
            for j, res_item in enumerate(result_copy):
                res_val = res_item.get(match_field)
                if self._values_match(exp_val, res_val):
                    matched_item = result_copy.pop(j)
                    match_id = f"{match_field}={self._truncate(exp_val)}"
                    break

            matches.append((exp_item, matched_item, match_id))

        # Add unmatched result items
        for j, res_item in enumerate(result_copy):
            res_val = res_item.get(match_field)
            match_id = f"extra_{match_field}={self._truncate(res_val)}"
            matches.append((None, res_item, match_id))

        return matches

    def _match_best_effort(
        self,
        expected_items: List[Dict],
        result_items: List[Dict],
        field_names: List[str],
    ) -> List[Tuple[Optional[Dict], Optional[Dict], str]]:
        """Best effort matching with fuzzy similarity."""
        matches = []
        result_copy = list(result_items)

        for i, exp_item in enumerate(expected_items):
            best_match = None
            best_score = 0.0
            best_idx = -1

            # Try to find best matching item
            for j, res_item in enumerate(result_copy):
                score = self._similarity_score(exp_item, res_item, field_names)
                if score > best_score:
                    best_score = score
                    best_match = res_item
                    best_idx = j

            # Use match if similarity > threshold
            if best_score > self.FUZZY_THRESHOLD and best_match:
                result_copy.pop(best_idx)
                matches.append(
                    (exp_item, best_match, f"fuzzy[{i}]_score={best_score:.2f}")
                )
            else:
                matches.append((exp_item, None, f"missing_exp[{i}]"))

        # Add remaining unmatched
        for j, res_item in enumerate(result_copy):
            matches.append((None, res_item, f"extra_actual[{j}]"))

        return matches

    def _similarity_score(
        self, item1: Dict, item2: Dict, field_names: List[str]
    ) -> float:
        """Calculate similarity between two items based on their fields."""
        scores = []
        for field in field_names:
            val1 = str(item1.get(field, ""))
            val2 = str(item2.get(field, ""))
            if val1 and val2:
                score = SequenceMatcher(None, val1, val2).ratio()
                scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _compare_field_across_matches(
        self,
        matches: List[Tuple[Optional[Dict], Optional[Dict], str]],
        field_name: str,
        array_field: str,
        comparison_type: str,
        matching_strategy: str,
    ) -> FieldComparison:
        """Compare a specific field across all matched pairs."""
        passed = 0
        failed = 0
        examples = []

        for exp_item, res_item, match_id in matches:
            if exp_item is None:
                # Extra item in result
                failed += 1
                if len(examples) < self.MAX_EXAMPLES:
                    examples.append(
                        ComparisonExample(
                            instance_identifier=match_id,
                            expected_value=None,
                            actual_value=self._serialize_value(
                                res_item.get(field_name) if res_item else None
                            ),
                            matched=False,
                            note="Extra item in actual output",
                        )
                    )
            elif res_item is None:
                # Missing item in result
                failed += 1
                if len(examples) < self.MAX_EXAMPLES:
                    examples.append(
                        ComparisonExample(
                            instance_identifier=match_id,
                            expected_value=self._serialize_value(
                                exp_item.get(field_name)
                            ),
                            actual_value=None,
                            matched=False,
                            note="Missing from actual output",
                        )
                    )
            else:
                # Both items present - compare field
                exp_val = exp_item.get(field_name)
                res_val = res_item.get(field_name)
                matched = self._values_match(exp_val, res_val)

                if matched:
                    passed += 1
                else:
                    failed += 1
                    if len(examples) < self.MAX_EXAMPLES:
                        examples.append(
                            ComparisonExample(
                                instance_identifier=match_id,
                                expected_value=self._serialize_value(exp_val),
                                actual_value=self._serialize_value(res_val),
                                matched=False,
                                note="Value mismatch",
                            )
                        )

        total = passed + failed
        field_path = f"{array_field}.{field_name}"

        return FieldComparison(
            field_path=field_path,
            comparison_type=comparison_type,
            total_instances=total,
            passed_instances=passed,
            failed_instances=failed,
            passed=(failed == 0),
            rationale=self._build_rationale(field_path, failed == 0, total, passed),
            examples=examples,
            matching_strategy=matching_strategy,
        )

    def _build_rationale(
        self, field_path: str, passed: bool, total: int, passed_count: int
    ) -> str:
        """Build human-readable rationale."""
        if passed:
            return f"All {total} instance(s) of '{field_path}' matched"
        else:
            failed_count = total - passed_count
            return f"{failed_count}/{total} instance(s) of '{field_path}' failed"

    def _values_match(self, val1: Any, val2: Any) -> bool:
        """Check if two values match with tolerance."""
        if val1 == val2:
            return True

        # Handle None vs empty string
        if val1 in (None, "") and val2 in (None, ""):
            return True

        # Handle numeric comparisons with tolerance
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return abs(val1 - val2) < 1e-9

        return False

    def _is_good_match(self, matches: List) -> bool:
        """Check if matching strategy produced good results."""
        if not matches:
            return False

        # At least 80% should have both items
        both_present = sum(1 for exp, res, _ in matches if exp and res)
        return both_present / len(matches) >= self.GOOD_MATCH_THRESHOLD

    def _to_dict(self, item: Any) -> Dict:
        """Convert item to dict if needed."""
        if isinstance(item, dict):
            return item
        elif hasattr(item, "model_dump"):
            return item.model_dump()
        elif hasattr(item, "__dict__"):
            return item.__dict__
        else:
            return {"value": item}

    def _truncate(self, value: Any, max_len: int | None = None) -> str:
        """Truncate string representation for display."""
        if max_len is None:
            max_len = self.TRUNCATE_LENGTH
        s = str(value)
        return s[:max_len] + "..." if len(s) > max_len else s

    def _serialize_value(self, value: Any) -> str:
        """Serialize a value to string for storage in ComparisonExample."""
        import json

        if value is None:
            return "null"
        if isinstance(value, str):
            return value
        if isinstance(value, (bool, int, float)):
            return json.dumps(value)

        # For complex objects, try JSON first, fall back to str
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)
