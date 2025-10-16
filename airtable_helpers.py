"""Shared Airtable helpers: field-name normalization and payload coercion.

These helpers centralize the normalization/mapping logic used in several
server variants so POST/PATCH flows normalize client keys, remap them to the
actual Airtable field names and coerce values based on schema metadata.
"""
import re
import unicodedata
import logging
from typing import List, Dict, Tuple, Any


def normalize_field_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    # Unicode normalize and remove common zero-width / invisibles
    n = unicodedata.normalize('NFKC', name)
    n = re.sub(r'[\u200B-\u200D\uFEFF]', '', n)
    n = re.sub(r'[\r\n\t]+', ' ', n)
    n = re.sub(r'\s+', ' ', n)
    return n.strip()


def coerce_payload_to_body(mapped_payload: Dict[str, Any], meta_fields: List[Dict]) -> Tuple[Dict, Dict]:
    """Coerce mapped_payload (keys are actual field names) into a body suitable
    for Airtable create/update. Returns (body, errors). meta_fields is a list of
    dicts with keys: name, type, choices (optional), required (optional).
    """
    errors = {}
    clean_body = {}
    if not isinstance(mapped_payload, dict):
        return mapped_payload or {}, {}

    meta_by_name = {mf["name"]: mf for mf in meta_fields}

    # Create a normalized mapping from incoming payload keys to actual field names
    normalized_payload_map = {
        normalize_field_name(k).lower(): k for k in mapped_payload.keys()
    }

    for airtable_field_name, meta_field in meta_by_name.items():
        normalized_airtable_field = normalize_field_name(airtable_field_name).lower()
        
        value = None
        # Find the corresponding key in the original payload
        if normalized_airtable_field in normalized_payload_map:
            original_key = normalized_payload_map[normalized_airtable_field]
            value = mapped_payload[original_key]

        # Fallback for direct match if normalization fails for some reason
        if value is None and airtable_field_name in mapped_payload:
            value = mapped_payload[airtable_field_name]

        # Skip if no value is provided and the field is not required
        if value is None or (isinstance(value, str) and not value.strip()):
            if meta_field.get("required"):
                errors[airtable_field_name] = "This field is required"
            continue

        field_type = meta_field.get("type", "text")

        try:
            if field_type in ("number", "percent", "currency"):
                clean_body[airtable_field_name] = float(value)
            elif field_type == "checkbox":
                clean_body[airtable_field_name] = str(value).lower() in ("true", "1", "on", "yes")
            elif field_type in ("singleSelect", "multipleSelects"):
                is_multiple = field_type == "multipleSelects"
                # Support multiple schema shapes: new: meta_field['options']['choices'],
                # older: meta_field['choices'] (list of names or dicts)
                choices = meta_field.get("options", {}).get("choices") or meta_field.get("choices") or []
                
                values_to_check = []
                if isinstance(value, list):
                    values_to_check = value
                elif isinstance(value, str):
                    values_to_check = [v.strip() for v in value.split(',')]
                else:
                    values_to_check = [str(value)]

                if not is_multiple and len(values_to_check) > 1:
                    values_to_check = [values_to_check[0]] # Take only the first value for singleSelect

                matched_choices = []
                unmatched_values = []
                logger = logging.getLogger(__name__)
                # Pre-compute lookup maps for faster and more flexible matching
                name_map = {}
                id_map = {}
                # Normalize choice entries: they can be dicts ({'id','name'}) or simple strings
                normalized_choices = []
                for c in choices:
                    if isinstance(c, dict):
                        cname = c.get("name")
                        cid = c.get("id")
                    else:
                        cname = str(c)
                        cid = None
                    if cname is None:
                        continue
                    normalized_choices.append({"name": cname, "id": cid})
                    name_map[normalize_field_name(cname).lower()] = cname
                    if cid is not None:
                        id_map[str(cid)] = cname

                matched_choices = []
                unmatched_values = []
                for v in values_to_check:
                    normalized_value = normalize_field_name(str(v)).lower()
                    found_choice = None

                    method = None
                    # 1) match by normalized name
                    if normalized_value in name_map:
                        found_choice = name_map[normalized_value]
                        method = "name"

                    # 2) match by explicit id (string)
                    if not found_choice and str(v) in id_map:
                        found_choice = id_map[str(v)]
                        method = "id"

                    # 3) if v looks like an integer, try index-based matching
                    if not found_choice:
                        try:
                            idx = int(str(v))
                        except Exception:
                            idx = None

                        if idx is not None and normalized_choices:
                            # try 1-based index (1 -> first choice)
                            if 1 <= idx <= len(normalized_choices):
                                found_choice = normalized_choices[idx - 1].get("name")
                                method = "index-1"
                            # try 0-based index (0 -> first choice)
                            elif 0 <= idx < len(normalized_choices):
                                found_choice = normalized_choices[idx].get("name")
                                method = "index-0"

                    if found_choice:
                        matched_choices.append(found_choice)
                        logger.debug("select-match: field=%r input=%r matched=%r method=%s", airtable_field_name, v, found_choice, method)
                    else:
                        unmatched_values.append(v)
                        logger.debug("select-unmatched: field=%r input=%r choices_count=%d", airtable_field_name, v, len(normalized_choices))

                if not unmatched_values:
                    clean_body[airtable_field_name] = matched_choices if is_multiple else matched_choices[0]
                else:
                    errors[airtable_field_name] = f"Invalid choice(s): {', '.join(map(str, unmatched_values))}"
            else:
                clean_body[airtable_field_name] = str(value)
        except (ValueError, TypeError) as e:
            errors[airtable_field_name] = f"Invalid value: {e}"

    # Add any keys from payload that were not in the metadata
    for key, val in mapped_payload.items():
        if key not in clean_body and key not in errors:
            # Check if a normalized version was already processed
            is_processed = False
            for meta_name in meta_by_name:
                if normalize_field_name(key).lower() == normalize_field_name(meta_name).lower():
                    is_processed = True
                    break
            if not is_processed:
                clean_body[key] = val

    return clean_body, errors
