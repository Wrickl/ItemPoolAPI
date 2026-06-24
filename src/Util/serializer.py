import json


def _serialize_text_payload(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)
