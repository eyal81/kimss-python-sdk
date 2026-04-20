"""
Optional PII redaction before requests (install kimss[privacy] and configure Presidio).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

BeforeRequestContext = Dict[str, Any]
BeforeRequestHook = Callable[[BeforeRequestContext], None]


class PresidioRedactor:
    """
    Pre-request hook that scrubs PII from chat payloads using Microsoft Presidio.

    Requires: pip install 'kimss[privacy]' (presidio-analyzer, presidio-anonymizer, spaCy model).

    Mutates ctx["json"] in place for keys like usr_chat and string values under parameters.
    """

    def __init__(
        self,
        *,
        entities: Optional[List[str]] = None,
        language: str = "en",
        score_threshold: float = 0.35,
    ) -> None:
        self.entities = entities or [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "US_SSN",
            "IP_ADDRESS",
        ]
        self.language = language
        self.score_threshold = score_threshold
        self._analyzer = None
        self._anonymizer = None

    def _ensure_presidio(self) -> None:
        if self._analyzer is not None:
            return
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
        except ImportError as e:
            raise ImportError(
                "Presidio is not installed. Use: pip install 'kimss[privacy]' "
                "and download a spaCy model (e.g. en_core_web_lg)."
            ) from e
        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()

    def __call__(self, ctx: BeforeRequestContext) -> None:
        self._ensure_presidio()
        assert self._analyzer is not None and self._anonymizer is not None
        payload = ctx.get("json")
        if not isinstance(payload, dict):
            return

        if "usr_chat" in payload and isinstance(payload["usr_chat"], str):
            payload["usr_chat"] = self._redact_text(str(payload["usr_chat"]))

        params = payload.get("parameters")
        if isinstance(params, dict):
            payload["parameters"] = self._redact_json_schema_strings(params)

        hdrs = ctx.get("headers")
        if isinstance(hdrs, dict):
            hdrs["x-kimss-pii-redacted"] = "true"

    def _redact_text(self, text: str) -> str:
        results = self._analyzer.analyze(  # type: ignore[union-attr]
            text=text,
            language=self.language,
            entities=self.entities,
            score_threshold=self.score_threshold,
        )
        return self._anonymizer.anonymize(text=text, analyzer_results=results).text  # type: ignore[union-attr]

    def _redact_json_schema_strings(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self._redact_text(obj)
        if isinstance(obj, dict):
            return {k: self._redact_json_schema_strings(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._redact_json_schema_strings(v) for v in obj]
        return obj
