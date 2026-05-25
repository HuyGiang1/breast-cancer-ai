import json
import os
import sys
import re
import base64
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request


CLINICAL_FEATURE_KEYS = [
    "mean_radius",
    "mean_texture",
    "mean_perimeter",
    "mean_area",
    "mean_smoothness",
    "mean_compactness",
    "mean_concavity",
    "mean_concave_points",
    "mean_symmetry",
    "mean_fractal_dimension",
    "radius_error",
    "texture_error",
    "perimeter_error",
    "area_error",
    "smoothness_error",
    "compactness_error",
    "concavity_error",
    "concave_points_error",
    "symmetry_error",
    "fractal_dimension_error",
    "worst_radius",
    "worst_texture",
    "worst_perimeter",
    "worst_area",
    "worst_smoothness",
    "worst_compactness",
    "worst_concavity",
    "worst_concave_points",
    "worst_symmetry",
    "worst_fractal_dimension",
]


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _build_feature_aliases() -> Dict[str, List[str]]:
    aliases: Dict[str, List[str]] = {}
    for key in CLINICAL_FEATURE_KEYS:
        spaced = key.replace("_", " ")
        values = {
            key,
            spaced,
            key.replace("_", ""),
            spaced.replace("points", "point"),
        }
        if key.endswith("_error"):
            values.add(spaced.replace(" error", " se"))
        aliases[key] = sorted(values, key=len, reverse=True)
    return aliases


FEATURE_ALIASES = _build_feature_aliases()


class AIAdvisorService:
    """Generate patient-facing recommendations from ML/DL outputs.

    If OPENAI_API_KEY is configured, this service can optionally call an external
    LLM endpoint compatible with OpenAI Chat Completions.
    """

    def __init__(self):
        self.provider = os.getenv("AI_ADVISOR_PROVIDER", "local").lower()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("AI_ADVISOR_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("AI_ADVISOR_BASE_URL", "https://api.openai.com/v1/chat/completions")
        self.timeout_seconds = int(os.getenv("AI_ADVISOR_TIMEOUT", "18"))
        self.gemini_api_key = (
            os.getenv("GEMINI_API_KEY", "").strip()
            or os.getenv("GOOGLE_API_KEY", "").strip()
        )
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.gemini_base_url = os.getenv(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/models",
        )
        self.ocr_local_order = [
            part.strip().lower()
            for part in os.getenv("OCR_LOCAL_ORDER", "tesseract,easyocr").split(",")
            if part.strip()
        ]
        self.easyocr_reader = None
        self.feature_aliases = FEATURE_ALIASES
        self.feature_aliases_norm = {
            key: [_normalize_for_match(alias) for alias in aliases]
            for key, aliases in self.feature_aliases.items()
        }

    def advice_for_single(self, result: Dict[str, Any], mode: str) -> Dict[str, str]:
        payload = {
            "mode": mode,
            "diagnosis": result.get("diagnosis"),
            "probability": float(result.get("probability", 0.0)),
            "risk_band": result.get("risk_band", "Medium"),
            "model_name": result.get("model_name", "Unknown"),
            "top_features": result.get("top_features") or [],
        }
        return self._generate_advice(payload, self._local_single)

    def chat_about_breast_cancer(self, message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, str]:
        prompt = self._build_chat_prompt(message=message, history=history or [])

        if self.provider == "gemini" and self.gemini_api_key:
            answer = self._call_gemini(prompt)
            if answer:
                return {"answer": answer, "provider": "gemini", "model": self.gemini_model}
            if self.api_key:
                answer = self._call_openai(prompt)
                if answer:
                    return {"answer": answer, "provider": "openai_fallback", "model": self.model}

        if self.provider == "openai" and self.api_key:
            answer = self._call_openai(prompt)
            if answer:
                return {"answer": answer, "provider": "openai", "model": self.model}
            if self.gemini_api_key:
                answer = self._call_gemini(prompt)
                if answer:
                    return {"answer": answer, "provider": "gemini_fallback", "model": self.gemini_model}

        return {
            "answer": self._local_chat(message),
            "provider": "local",
            "model": "rule-based-advisor",
        }

    def advice_for_multimodal(
        self,
        ml_result: Dict[str, Any],
        dl_result: Dict[str, Any],
        combined_probability: float,
    ) -> Dict[str, str]:
        payload = {
            "mode": "multimodal",
            "combined_probability": float(combined_probability),
            "combined_risk_band": self._risk_band(float(combined_probability)),
            "ml": {
                "diagnosis": ml_result.get("diagnosis"),
                "probability": float(ml_result.get("probability", 0.0)),
                "risk_band": ml_result.get("risk_band", "Medium"),
                "model_name": ml_result.get("model_name", "Unknown"),
                "top_features": ml_result.get("top_features") or [],
            },
            "dl": {
                "diagnosis": dl_result.get("diagnosis"),
                "probability": float(dl_result.get("probability", 0.0)),
                "risk_band": dl_result.get("risk_band", "Medium"),
                "model_name": dl_result.get("model_name", "Unknown"),
            },
        }

        return self._generate_advice(payload, self._local_multimodal)

    def extract_clinical_features_from_image(
        self,
        image_bytes: bytes,
        content_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        prompt = self._clinical_extraction_prompt()
        best_candidate: Optional[Tuple[Dict[str, Any], str, str, str]] = None
        best_filled = -1

        # 1) Local OCR first (Tesseract/EasyOCR) + regex mapping.
        local = self._extract_clinical_features_local_ocr(image_bytes)
        if local is not None:
            parsed, provider, model, raw_text = local
            filled = sum(v is not None for v in parsed.values())
            best_candidate = local
            best_filled = filled
            if filled == len(CLINICAL_FEATURE_KEYS):
                return self._build_clinical_extraction_response(parsed, provider, model, raw_text)

        # 2) Fallback to external vision LLM only when local OCR is insufficient.
        llm_candidates: List[Tuple[Dict[str, Any], str, str, str]] = []
        if self.provider == "gemini" and self.gemini_api_key:
            text = self._call_gemini_with_image(prompt, image_bytes, content_type)
            parsed = self._parse_clinical_feature_json(text)
            if parsed:
                llm_candidates.append((parsed, "gemini", self.gemini_model, text))
            if self.api_key:
                text = self._call_openai_with_image(prompt, image_bytes, content_type)
                parsed = self._parse_clinical_feature_json(text)
                if parsed:
                    llm_candidates.append((parsed, "openai_fallback", self.model, text))
        elif self.provider == "openai" and self.api_key:
            text = self._call_openai_with_image(prompt, image_bytes, content_type)
            parsed = self._parse_clinical_feature_json(text)
            if parsed:
                llm_candidates.append((parsed, "openai", self.model, text))
            if self.gemini_api_key:
                text = self._call_gemini_with_image(prompt, image_bytes, content_type)
                parsed = self._parse_clinical_feature_json(text)
                if parsed:
                    llm_candidates.append((parsed, "gemini_fallback", self.gemini_model, text))

        for candidate in llm_candidates:
            parsed, _, _, _ = candidate
            filled = sum(v is not None for v in parsed.values())
            if filled > best_filled:
                best_candidate = candidate
                best_filled = filled
                if filled == len(CLINICAL_FEATURE_KEYS):
                    break

        if best_candidate is not None and best_filled > 0:
            parsed, provider, model, raw_text = best_candidate
            return self._build_clinical_extraction_response(parsed, provider, model, raw_text)

        raise RuntimeError(
            "Không trích xuất được chỉ số từ ảnh. Hãy thử ảnh rõ hơn hoặc kiểm tra cấu hình OCR/AI."
        )

    def _extract_clinical_features_local_ocr(
        self,
        image_bytes: bytes,
    ) -> Optional[Tuple[Dict[str, Any], str, str, str]]:
        best: Optional[Tuple[Dict[str, Any], str, str, str]] = None
        best_filled = -1

        for engine in self.ocr_local_order:
            text = ""
            provider = ""
            model = ""
            if engine == "tesseract":
                text = self._ocr_with_tesseract(image_bytes)
                provider = "local_ocr_tesseract"
                model = "pytesseract"
            elif engine == "easyocr":
                text = self._ocr_with_easyocr(image_bytes)
                provider = "local_ocr_easyocr"
                model = "easyocr"
            else:
                continue

            if not text.strip():
                continue

            parsed = self._parse_clinical_feature_ocr_text(text)
            filled = sum(v is not None for v in parsed.values())
            if filled > best_filled:
                best = (parsed, provider, model, text)
                best_filled = filled
                if filled == len(CLINICAL_FEATURE_KEYS):
                    return best

        return best

    def _ocr_with_tesseract(self, image_bytes: bytes) -> str:
        try:
            import cv2
            import numpy as np
            import pytesseract

            tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is None:
                return ""
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9
            )
            variants = [gray, otsu, adaptive]
            config = os.getenv("OCR_TESSERACT_CONFIG", "--oem 3 --psm 6")
            texts: List[str] = []
            for variant in variants:
                txt = pytesseract.image_to_string(variant, config=config).strip()
                if txt:
                    texts.append(txt)
            return "\n\n".join(texts).strip()
        except Exception as exc:
            self._log_external_error("Local OCR (tesseract)", exc)
            return ""

    def _ocr_with_easyocr(self, image_bytes: bytes) -> str:
        try:
            import cv2
            import numpy as np
            import easyocr

            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is None:
                return ""
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            if self.easyocr_reader is None:
                self.easyocr_reader = easyocr.Reader(["en"], gpu=False)

            texts: List[str] = []
            for variant in (image, gray):
                result = self.easyocr_reader.readtext(variant, detail=0, paragraph=False)
                if result:
                    texts.append("\n".join(str(item) for item in result))
            return "\n\n".join(texts).strip()
        except Exception as exc:
            self._log_external_error("Local OCR (easyocr)", exc)
            return ""

    def _extract_numeric_tokens(self, text: str) -> List[float]:
        tokens = re.findall(r"[-+]?\d+(?:[.,]\d+)?(?:e[-+]?\d+)?", text, flags=re.IGNORECASE)
        values: List[float] = []
        for token in tokens:
            normalized = token.replace(",", ".")
            try:
                values.append(float(normalized))
            except ValueError:
                continue
        return values

    def _parse_clinical_feature_ocr_text(self, text: str) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {key: None for key in CLINICAL_FEATURE_KEYS}
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # Pass 1: line-level fuzzy match.
        for line in lines:
            line_norm = _normalize_for_match(line)
            values = self._extract_numeric_tokens(line)
            if not values:
                continue
            for key in CLINICAL_FEATURE_KEYS:
                if parsed[key] is not None:
                    continue
                aliases = self.feature_aliases_norm.get(key, [])
                if any(alias and alias in line_norm for alias in aliases):
                    parsed[key] = values[0]
                    break

        # Pass 2: global regex for remaining fields.
        lower_text = text.lower()
        for key in CLINICAL_FEATURE_KEYS:
            if parsed[key] is not None:
                continue
            for alias in self.feature_aliases.get(key, []):
                alias_pattern = re.escape(alias.lower()).replace(r"\ ", r"\s*")
                match = re.search(
                    rf"{alias_pattern}[^\d\-+]*([-+]?\d+(?:[.,]\d+)?(?:e[-+]?\d+)?)",
                    lower_text,
                    flags=re.IGNORECASE,
                )
                if not match:
                    continue
                token = match.group(1).replace(",", ".")
                try:
                    parsed[key] = float(token)
                    break
                except ValueError:
                    continue

        return parsed

    def _risk_band(self, p: float) -> str:
        if p < 0.35:
            return "Low"
        if p < 0.65:
            return "Medium"
        return "High"

    def _call_external(self, payload: Dict[str, Any]) -> str:
        prompt = self._external_prompt(payload)

        if self.provider == "gemini" and self.gemini_api_key:
            return self._call_gemini(prompt)

        if self.provider == "openai" and self.api_key:
            return self._call_openai(prompt)

        return ""

    def _external_prompt(self, payload: Dict[str, Any]) -> str:
        return (
            "You are a clinical assistant for breast cancer screening support. "
            "Return concise Vietnamese advice in 4 bullets: risk summary, immediate next tests, "
            "follow-up timeline, and patient lifestyle notes. Include a disclaimer that this is not a diagnosis. "
            f"Case payload: {json.dumps(payload, ensure_ascii=False)}"
        )

    def _generate_advice(self, payload: Dict[str, Any], local_generator) -> Dict[str, str]:
        prompt = self._external_prompt(payload)
        if self.provider == "gemini" and self.gemini_api_key:
            advice = self._call_gemini(prompt)
            if advice:
                return {"advice": advice, "provider": "gemini", "model": self.gemini_model}
            if self.api_key:
                advice = self._call_openai(prompt)
                if advice:
                    return {"advice": advice, "provider": "openai_fallback", "model": self.model}
            return {
                "advice": local_generator(payload),
                "provider": "local_fallback",
                "model": "rule-based-advisor",
            }

        if self.provider == "openai" and self.api_key:
            advice = self._call_openai(prompt)
            if advice:
                return {"advice": advice, "provider": "openai", "model": self.model}
            if self.gemini_api_key:
                advice = self._call_gemini(prompt)
                if advice:
                    return {"advice": advice, "provider": "gemini_fallback", "model": self.gemini_model}
            return {
                "advice": local_generator(payload),
                "provider": "local_fallback",
                "model": "rule-based-advisor",
            }

        return {
            "advice": local_generator(payload),
            "provider": "local",
            "model": "rule-based-advisor",
        }

    def _build_chat_prompt(self, message: str, history: List[Dict[str, str]]) -> str:
        history_lines: List[str] = []
        for item in history[-8:]:
            role = str(item.get("role", "user")).strip() or "user"
            content = str(item.get("content", "")).strip()
            if content:
                history_lines.append(f"{role}: {content}")

        history_block = "\n".join(history_lines) if history_lines else "No prior conversation."
        return (
            "You are a safe Vietnamese health information assistant focused on breast cancer education. "
            "Answer in Vietnamese, clearly, practically, and empathetically. "
            "Do not claim to diagnose. If symptoms are urgent or suspicious, advise clinical evaluation. "
            "Keep answers concise but useful. Prefer short sections when helpful. "
            "If the user asks outside breast cancer, gently redirect back to breast health and screening support.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"Current user message:\n{message}"
        )

    def _call_openai(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You provide safe, concise, non-definitive medical guidance."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        req = request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
        except error.HTTPError as exc:
            self._log_external_error("OpenAI", exc)
            return ""
        except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            self._log_external_error("OpenAI", exc)
            return ""

    def _call_openai_with_image(self, prompt: str, image_bytes: bytes, content_type: str) -> str:
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You extract structured clinical values from medical forms and reply with strict JSON only."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{content_type};base64,{image_b64}"},
                        },
                    ],
                },
            ],
            "temperature": 0.0,
        }

        req = request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
        except error.HTTPError as exc:
            self._log_external_error("OpenAI image", exc)
            return ""
        except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            self._log_external_error("OpenAI image", exc)
            return ""

    def _call_gemini(self, prompt: str) -> str:
        url = f"{self.gemini_base_url}/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        body = {
            "systemInstruction": {
                "parts": [
                    {"text": "You provide safe, concise, non-definitive medical guidance in Vietnamese."}
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
            },
        }

        req = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            candidates = data.get("candidates", [])
            if not candidates:
                return ""

            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [part.get("text", "").strip() for part in parts if part.get("text")]
            return "\n".join(part for part in text_parts if part).strip()
        except error.HTTPError as exc:
            self._log_external_error("Gemini", exc)
            return ""
        except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            self._log_external_error("Gemini", exc)
            return ""

    def _call_gemini_with_image(self, prompt: str, image_bytes: bytes, content_type: str) -> str:
        url = f"{self.gemini_base_url}/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        body = {
            "systemInstruction": {
                "parts": [
                    {"text": "You extract structured clinical values from medical forms and reply with strict JSON only."}
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": content_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
            },
        }

        req = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            candidates = data.get("candidates", [])
            if not candidates:
                return ""

            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [part.get("text", "").strip() for part in parts if part.get("text")]
            return "\n".join(part for part in text_parts if part).strip()
        except error.HTTPError as exc:
            self._log_external_error("Gemini image", exc)
            return ""
        except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            self._log_external_error("Gemini image", exc)
            return ""

    def _log_external_error(self, provider: str, exc: Exception) -> None:
        try:
            if isinstance(exc, error.HTTPError):
                body = exc.read().decode("utf-8", errors="replace")
                print(
                    f"[AIAdvisor] {provider} HTTPError {exc.code}: {body}",
                    file=sys.stderr,
                )
                return
            print(f"[AIAdvisor] {provider} error: {exc}", file=sys.stderr)
        except Exception as log_exc:
            print(f"[AIAdvisor] Failed to log {provider} error: {log_exc}", file=sys.stderr)

    def _clinical_extraction_prompt(self) -> str:
        alias_lines = "\n".join(
            [
                "mean_radius => mean radius",
                "mean_texture => mean texture",
                "mean_perimeter => mean perimeter",
                "mean_area => mean area",
                "mean_smoothness => mean smoothness",
                "mean_compactness => mean compactness",
                "mean_concavity => mean concavity",
                "mean_concave_points => mean concave points",
                "mean_symmetry => mean symmetry",
                "mean_fractal_dimension => mean fractal dimension",
                "radius_error => radius error",
                "texture_error => texture error",
                "perimeter_error => perimeter error",
                "area_error => area error",
                "smoothness_error => smoothness error",
                "compactness_error => compactness error",
                "concavity_error => concavity error",
                "concave_points_error => concave points error",
                "symmetry_error => symmetry error",
                "fractal_dimension_error => fractal dimension error",
                "worst_radius => worst radius",
                "worst_texture => worst texture",
                "worst_perimeter => worst perimeter",
                "worst_area => worst area",
                "worst_smoothness => worst smoothness",
                "worst_compactness => worst compactness",
                "worst_concavity => worst concavity",
                "worst_concave_points => worst concave points",
                "worst_symmetry => worst symmetry",
                "worst_fractal_dimension => worst fractal dimension",
            ]
        )
        empty_json = ",\n".join([f'  "{key}": null' for key in CLINICAL_FEATURE_KEYS])
        return (
            "Read the uploaded breast-cancer clinical report image and extract the 30 numeric feature values. "
            "Return strict JSON only, with no markdown, no commentary, and no extra keys. "
            "Use the snake_case keys exactly as listed below. "
            "If a value cannot be found with confidence, set it to null. "
            "Accept decimal values. Ignore patient identity, diagnosis text, headers, and unrelated notes.\n\n"
            f"Key mapping:\n{alias_lines}\n\n"
            "Return exactly this JSON shape:\n"
            "{\n"
            f"{empty_json}\n"
            "}"
        )

    def _parse_clinical_feature_json(self, text: str) -> Dict[str, Any] | None:
        if not text:
            return None
        candidate = text.strip()
        candidate = re.sub(r"^```json\s*", "", candidate)
        candidate = re.sub(r"^```\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
        if "{" in candidate and "}" in candidate:
            candidate = candidate[candidate.find("{"):candidate.rfind("}") + 1]
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        parsed: Dict[str, Any] = {}
        for key in CLINICAL_FEATURE_KEYS:
            value = payload.get(key)
            if value in ("", "null", None):
                parsed[key] = None
                continue
            try:
                parsed[key] = float(value)
            except (TypeError, ValueError):
                parsed[key] = None
        return parsed

    def _build_clinical_extraction_response(
        self,
        parsed: Dict[str, Any],
        provider: str,
        model: str,
        raw_text: str,
    ) -> Dict[str, Any]:
        return {
            "values": parsed,
            "filled_count": sum(v is not None for v in parsed.values()),
            "missing_fields": [k for k, v in parsed.items() if v is None],
            "provider": provider,
            "model": model,
            "raw_text": raw_text,
        }

    def _local_single(self, payload: Dict[str, Any]) -> str:
        diag = payload.get("diagnosis", "Unknown")
        prob = float(payload.get("probability", 0.0))
        risk = payload.get("risk_band", "Medium")
        model_name = payload.get("model_name", "Unknown")
        mode = payload.get("mode", "ml")

        feature_text = ""
        top_features: List[Dict[str, Any]] = payload.get("top_features") or []
        if top_features:
            names = [str(item.get("feature", "")) for item in top_features[:3] if item.get("feature")]
            if names:
                feature_text = f" Các chỉ số nổi bật: {', '.join(names)}."

        if diag == "Malignant":
            return (
                f"AI Advisor ({model_name}, {mode.upper()}): Nguy cơ hiện ở mức {risk} ({prob*100:.1f}%)."
                " Khuyến nghị đi khám chuyên khoa ung bướu/senology trong 24-72 giờ và thực hiện thêm chẩn đoán xác nhận"
                " như siêu âm, mammography hoặc sinh thiết theo chỉ định bác sĩ."
                " Trong thời gian chờ khám, theo dõi triệu chứng và không tự kết luận điều trị."
                f"{feature_text}"
                " Lưu ý: Đây là hệ thống hỗ trợ quyết định, không thay thế chẩn đoán y khoa."
            )

        return (
            f"AI Advisor ({model_name}, {mode.upper()}): Kết quả hiện nghiêng về lành tính với mức nguy cơ {risk} ({prob*100:.1f}%)."
            " Bạn vẫn nên tái khám định kỳ và đi khám sớm nếu có dấu hiệu bất thường (khối cứng tăng nhanh, đau kéo dài, tiết dịch núm vú)."
            f"{feature_text}"
            " Lưu ý: Đây là hệ thống hỗ trợ quyết định, không thay thế chẩn đoán y khoa."
        )

    def _local_multimodal(self, payload: Dict[str, Any]) -> str:
        p = float(payload.get("combined_probability", 0.0))
        band = payload.get("combined_risk_band", "Medium")
        ml = payload.get("ml", {})
        dl = payload.get("dl", {})

        return (
            f"AI Advisor (Integrated): Nguy cơ tổng hợp ở mức {band} ({p*100:.1f}%), "
            f"ML={float(ml.get('probability', 0.0))*100:.1f}% và DL={float(dl.get('probability', 0.0))*100:.1f}%. "
            "Nếu nguy cơ trung bình-cao, nên khám chuyên khoa để làm xét nghiệm xác nhận và đối chiếu với tiền sử cá nhân. "
            "Nếu nguy cơ thấp, tiếp tục tầm soát định kỳ theo lịch bác sĩ. "
            "Lưu ý: Đây là hệ thống hỗ trợ quyết định, không thay thế chẩn đoán y khoa."
        )

    def _local_chat(self, message: str) -> str:
        text = message.lower()
        if any(keyword in text for keyword in ["triệu chứng", "dấu hiệu", "đau", "khối", "tiết dịch"]):
            return (
                "Các dấu hiệu nên đi khám sớm gồm: sờ thấy khối cứng ở vú hoặc nách, thay đổi da kiểu lõm hoặc sần, "
                "núm vú tụt mới xuất hiện, tiết dịch bất thường, hoặc đau khu trú kéo dài. "
                "Nếu bạn đang có một trong các dấu hiệu này, nên khám chuyên khoa sớm. "
                "Lưu ý: đây không phải chẩn đoán y khoa."
            )
        if any(keyword in text for keyword in ["ăn gì", "dinh dưỡng", "thực phẩm", "kiêng"]):
            return (
                "Nên ưu tiên khẩu phần cân bằng với rau xanh, trái cây chín, đạm nạc, cá giàu omega-3, họ đậu và đủ nước. "
                "Hạn chế rượu bia, đồ uống quá ngọt, thịt chế biến sẵn và món chiên nhiều dầu. "
                "Nếu đang điều trị, nên hỏi bác sĩ hoặc chuyên gia dinh dưỡng trước khi thay đổi chế độ ăn lớn. "
                "Lưu ý: đây là thông tin hỗ trợ, không thay thế tư vấn điều trị."
            )
        return (
            "Tôi có thể hỗ trợ về dấu hiệu nghi ngờ ung thư vú, sàng lọc, nhũ ảnh, dinh dưỡng, phục hồi sau điều trị và cách chuẩn bị đi khám. "
            "Bạn có thể hỏi cụ thể hơn, ví dụ: 'Dấu hiệu nào cần đi khám sớm?' hoặc 'Người nghi ung thư vú nên ăn gì?'. "
            "Lưu ý: tôi không thay thế bác sĩ và không đưa ra chẩn đoán xác định."
        )


ai_advisor_service = AIAdvisorService()
