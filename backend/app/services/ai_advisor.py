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
            return {
                "answer": self._local_chat(message),
                "provider": "local",
                "model": "rule-based-advisor",
            }

        if self.provider == "openai" and self.api_key:
            answer = self._call_openai(prompt)
            if answer:
                return {"answer": answer, "provider": "openai", "model": self.model}

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
        branch_agreement = bool(ml_result.get("diagnosis") == dl_result.get("diagnosis"))
        payload = {
            "mode": "multimodal",
            "combined_probability": float(combined_probability),
            "combined_risk_band": self._risk_band(float(combined_probability)),
            "branch_agreement": branch_agreement,
            "branches_unpaired": True,
            "ml": {
                "diagnosis": ml_result.get("diagnosis"),
                "raw_probability": float(ml_result.get("raw_probability", ml_result.get("probability", 0.0))),
                "probability": float(ml_result.get("probability", 0.0)),
                "threshold": float(ml_result.get("decision_threshold", 0.36)),
                "risk_band": ml_result.get("risk_band", "Medium"),
                "model_name": ml_result.get("model_name", "Unknown"),
                "top_features": ml_result.get("top_features") or [],
            },
            "dl": {
                "diagnosis": dl_result.get("diagnosis"),
                "raw_probability": float(dl_result.get("raw_probability", 0.0)),
                "probability": float(dl_result.get("probability", 0.0)),
                "calibrated_probability": float(dl_result.get("calibrated_probability", dl_result.get("probability", 0.0))),
                "threshold": float(dl_result.get("decision_threshold", 0.515)),
                "risk_band": dl_result.get("risk_band", "Medium"),
                "model_name": dl_result.get("model_name", "Unknown"),
                "explanation_status": dl_result.get("explanation_status", "unavailable"),
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
        elif self.provider == "openai" and self.api_key:
            text = self._call_openai_with_image(prompt, image_bytes, content_type)
            parsed = self._parse_clinical_feature_json(text)
            if parsed:
                llm_candidates.append((parsed, "openai", self.model, text))

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
        if payload.get("mode") == "multimodal":
            return (
                "You are an educational AI assistant for experimental multimodal research. "
                "Provide concise Vietnamese guidance in 4 clear points: "
                "1) Structured ML branch review (WDBC), 2) Mammography DL branch review (CBIS-DDSM), "
                "3) Agreement/disagreement synthesis with explicit unpaired dataset warning "
                "(WDBC and CBIS-DDSM are unpaired observations; this software combination is NOT a validated clinical model), "
                "and 4) Educational recommendation emphasizing clinical consultation. "
                "CRITICAL: If the branches disagree, state that the software combination cannot resolve the disagreement as a diagnosis. "
                "Never claim one model confirms or overrules the other. "
                f"Case payload: {json.dumps(payload, ensure_ascii=False)}"
            )

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
            return {
                "advice": local_generator(payload),
                "provider": "local",
                "model": "rule-based-advisor",
            }

        if self.provider == "openai" and self.api_key:
            advice = self._call_openai(prompt)
            if advice:
                return {"advice": advice, "provider": "openai", "model": self.model}
            return {
                "advice": local_generator(payload),
                "provider": "local",
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
            "You are Breast Health Studio AI Guide — an educational and research assistant for breast cancer machine learning and imaging exploration.\n\n"
            "=== SCIENTIFIC GROUND TRUTHS & PROJECT SPECIFICATIONS ===\n"
            "1. STUDY A (WDBC - Wisconsin Diagnostic Breast Cancer):\n"
            "   - Exactly 569 fine needle aspirate (FNA) biopsy samples.\n"
            "   - Exactly 30 numerical features measuring cell nucleus morphology (radius, texture, perimeter, area, smoothness, compactness, concavity, concave points, symmetry, fractal dimension across mean, standard error, and worst groups).\n"
            "   - CRITICAL TRUTH: These 30 features are FNA nuclear cytology measurements, NOT blood tests, laboratory blood panels, or nutritional values.\n"
            "   - Primary frozen research model: Logistic Regression (StandardScaler -> LogisticRegression).\n"
            "   - Decision threshold: raw malignant probability >= 0.360. This is a research software decision cutoff, NOT a clinical threshold.\n"
            "   - SHAP (SHapley Additive exPlanations): post-hoc feature contribution explanation measuring standardized log-odds impact toward benign or malignant prediction. SHAP is non-causal and purely descriptive.\n\n"
            "2. STUDY B (CBIS-DDSM - Digital Mammography):\n"
            "   - Evaluates digital mammography scans.\n"
            "   - Primary frozen model: EfficientNet-B0 trained on full processed images.\n"
            "   - Decision threshold: raw malignant probability >= 0.515.\n"
            "   - Platt calibration is reliability/display calibration only; it does not replace the raw 0.515 decision cutoff.\n"
            "   - Grad-CAM layer: top_conv. Grad-CAM provides qualitative, coarse visual attention heatmaps showing which image regions activated the model. It is NOT lesion segmentation, NOT tumor localization, and NOT pathology ground truth. Red heat does NOT equal cancer location.\n\n"
            "3. EXPERIMENTAL FUSION WORKSTATION:\n"
            "   - WDBC (cytology) and CBIS-DDSM (mammography) are independent, completely UNPAIRED datasets (never sampled from the same patients).\n"
            "   - Software heuristic formula: Combined Score = 0.40 * ML_raw_probability + 0.60 * DL_raw_probability.\n"
            "   - Software decision midpoint: 0.50 (50.0%).\n"
            "   - CRITICAL TRUTH: Fusion is an experimental software heuristic for university research demonstration. It is NOT a clinically validated multimodal diagnostic model. If branches disagree, the combined score cannot resolve the disagreement.\n"
            "   - A fusion score of 80% does NOT mean an individual has an 80% chance of cancer; it is merely a mathematical combination score of unpaired research models.\n\n"
            "4. WORKSPACE ROLES & CLINICAL BOUNDARIES:\n"
            "   - The 'Doctor' role is self-declared for research/demo purposes; the system does not verify medical licenses.\n"
            "   - This platform CANNOT replace a doctor or specialist clinical examination, diagnostic mammography, or tissue biopsy.\n\n"
            "=== STRICT SAFETY & COMPLIANCE GUARDRAILS ===\n"
            "- NEVER diagnose or state whether someone definitely has or does not have cancer.\n"
            "- NEVER prescribe medications, surgical procedures, or specific clinical therapies.\n"
            "- If user asks 'Do I have cancer?' or asks for diagnosis: clearly state you cannot diagnose, and explain that formal clinical examination and pathology biopsy are required.\n"
            "- If user asks if Grad-CAM marks the tumor/cancer location: explicitly answer NO, and explain attention heatmap limitations.\n"
            "- If user asks if Fusion score equals personal cancer risk: explicitly answer NO, and explain unpaired datasets and software heuristic nature.\n"
            "- If user asks if this software can replace a doctor: explicitly answer NO.\n\n"
            "=== LANGUAGE & TONE ===\n"
            "- Default to natural, clear, academic Vietnamese appropriate for university students and lecturers.\n"
            "- If the user asks in English, reply in English.\n"
            "- Keep responses concise, well-structured, and educational.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"User question:\n{message}"
        )

    def _call_openai(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Breast Health Studio AI Guide, an educational and research prototype assistant for breast cancer machine learning and imaging exploration.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        req = request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
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
            err_body = exc.read().decode("utf-8", errors="replace")
            # If model-parameter compatibility issue (e.g. temperature or system message rejected)
            if exc.code == 400 and ("temperature" in err_body.lower() or "system" in err_body.lower()):
                body_compat = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "developer",
                            "content": "You are Breast Health Studio AI Guide, an educational and research prototype assistant.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                }
                req_compat = request.Request(
                    self.base_url,
                    data=json.dumps(body_compat).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                try:
                    with request.urlopen(req_compat, timeout=self.timeout_seconds) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    return (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                except Exception as inner_exc:
                    self._log_external_error("OpenAI (compat retry)", inner_exc)
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

        for attempt in range(2):
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
                if exc.code == 503 and attempt == 0:
                    import time
                    time.sleep(1.2)
                    continue
                self._log_external_error("Gemini", exc)
                return ""
            except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
                self._log_external_error("Gemini", exc)
                return ""
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
                body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
                if self.api_key:
                    body = body.replace(self.api_key, "[REDACTED]")
                print(
                    f"[AIAdvisor] {provider} HTTPError {exc.code}: {body}",
                    file=sys.stderr,
                )
                return
            err_msg = str(exc)
            if self.api_key:
                err_msg = err_msg.replace(self.api_key, "[REDACTED]")
            print(f"[AIAdvisor] {provider} error: {err_msg}", file=sys.stderr)
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
        ml = payload.get("ml", {})
        dl = payload.get("dl", {})
        ml_diag = ml.get("diagnosis", "Benign")
        dl_diag = dl.get("diagnosis", "Benign")
        ml_prob = float(ml.get("raw_probability", ml.get("probability", 0.0)))
        dl_prob = float(dl.get("raw_probability", 0.0))
        agreement = payload.get("branch_agreement", ml_diag == dl_diag)

        if not agreement:
            return (
                f"AI Educational Guidance (Bất đồng nhánh): Hai nhánh nghiên cứu cho kết quả không đồng thuận "
                f"(Nhánh ML FNA: {ml_diag}, xác suất thô {ml_prob*100:.1f}%; Nhánh DL ảnh nhũ ảnh: {dl_diag}, xác suất thô {dl_prob*100:.1f}%). "
                f"Điểm kết hợp phần mềm thực nghiệm (40/60) là {p*100:.1f}%. "
                "Vì mô hình ML (tập WDBC) và DL (tập CBIS-DDSM) được huấn luyện độc lập trên các tập dữ liệu không ghép cặp (unpaired), "
                "công thức kết hợp thực nghiệm này không thể và không được dùng để phân xử bất đồng giữa hai nhánh. "
                "Bất đồng này đòi hỏi thăm khám chuyên khoa trực tiếp và đối chiếu hình ảnh/giải phẫu bệnh từ bác sĩ. "
                "Lưu ý: Kết quả mang tính chất nghiên cứu phần mềm, không phải chẩn đoán y khoa."
            )

        return (
            f"AI Educational Guidance (Đồng thuận nhánh): Cả hai nhánh nghiên cứu độc lập cùng cho chỉ dấu {ml_diag} "
            f"(Nhánh ML FNA: {ml_prob*100:.1f}%, Nhánh DL ảnh: {dl_prob*100:.1f}%). "
            f"Điểm kết hợp phần mềm thực nghiệm (40/60) là {p*100:.1f}%. "
            "Lưu ý rằng sự đồng thuận giữa hai nhánh không đồng nghĩa với chẩn đoán y khoa đã xác thực, "
            "do dữ liệu đầu vào không ghép cặp từ cùng một cá nhân trong quá trình huấn luyện mô hình. "
            "Người dùng nên đối chiếu với kết luận từ bác sĩ chuyên khoa và xét nghiệm cận lâm sàng chính thức."
        )

    def _local_chat(self, message: str) -> str:
        text = message.lower()

        # Scientific Truth A: WDBC definition
        if "wdbc" in text and any(w in text for w in ["là gì", "la gi", "what is", "nghĩa là", "tap du lieu", "tập dữ liệu"]):
            return (
                "WDBC (Wisconsin Diagnostic Breast Cancer) là một tập dữ liệu nghiên cứu kinh điển gồm 569 mẫu sinh thiết hút kim nhỏ (FNA). "
                "Tập dữ liệu chứa đúng 30 đặc trưng số học mô tả hình thái nhân tế bào (như bán kính, kết cấu, chu vi, diện tích, độ mịn, độ co đặc, độ lõm, điểm lõm, tính đối xứng và số chiều fractal). "
                "Lưu ý khoa học quan trọng: Đây là các đặc trưng hình thái tế bào học FNA từ ảnh số hóa, HOÀN TOÀN KHÔNG PHẢI là xét nghiệm máu, chỉ số sinh hóa máu hay thành phần dinh dưỡng."
            )

        # Scientific Truth B: Threshold 0.36
        if "0.36" in text and any(w in text for w in ["threshold", "ngưỡng", "nghia la", "nghĩa là", "ml"]):
            return (
                "Ngưỡng 0.360 (36.0%) là ngưỡng quyết định (decision threshold) phần mềm được cố định cho mô hình Logistic Regression trên tập dữ liệu tế bào học WDBC. "
                "Khi xác suất ác tính thô (raw malignant probability) đạt từ 0.360 trở lên, mô hình phần mềm sẽ phân loại mẫu là Ác tính (Malignant). "
                "Đây là một ngưỡng quyết định kỹ thuật phần mềm phục vụ nghiên cứu và trình diễn thuật toán nhằm tối ưu độ nhạy, KHÔNG PHẢI là ngưỡng chẩn đoán y khoa chính thức trên lâm sàng."
            )

        # Scientific Truth C: Grad-CAM red attention
        if "grad-cam" in text or "gradcam" in text:
            if any(w in text for w in ["đỏ", "do", "vị trí", "vi tri", "khối u", "khoi u", "ung thư", "ung thu", "lesion", "tumor"]):
                return (
                    "KHÔNG. Vùng màu đỏ trên bản đồ nhiệt Grad-CAM KHÔNG PHẢI là vị trí khối u hay bằng chứng giải phẫu bệnh của ung thư. "
                    "Grad-CAM (từ tầng top_conv của EfficientNet-B0) chỉ là một công cụ giải thích trực quan định tính, thể hiện vùng ảnh mà mạng nơ-ron tập trung kích hoạt cao nhất khi đưa ra dự đoán. "
                    "Nó không có chức năng phân vùng ranh giới khối u (lesion segmentation) hay định vị tổn thương y khoa chính xác. Việc xác định vị trí tổn thương thực tế phải do bác sĩ chẩn đoán hình ảnh thực hiện."
                )
            return (
                "Grad-CAM là kỹ thuật trực quan hóa định tính trích xuất từ tầng top_conv của mô hình EfficientNet-B0. "
                "Nó hiển thị bản đồ chú ý của mạng nơ-ron nhân tạo trên ảnh nhũ ảnh số hóa, giúp nghiên cứu viên hiểu mô hình dựa vào vùng nào để phân loại, "
                "nhưng KHÔNG dùng để định vị khối u hay thay thế đánh giá giải phẫu bệnh."
            )

        # Scientific Truth D: Fusion 80%
        if "fusion" in text and ("80%" in text or "80" in text):
            return (
                "KHÔNG. Điểm số Fusion 80% KHÔNG ĐỒNG NGHĨA với việc bạn có 80% khả năng hoặc nguy cơ bị ung thư. "
                "Tập dữ liệu tế bào học WDBC và tập ảnh nhũ ảnh CBIS-DDSM là hai nguồn nghiên cứu hoàn toàn độc lập, không ghép cặp (unpaired) từ cùng một bệnh nhân. "
                "Công thức kết hợp 40% ML + 60% DL chỉ là một ước lượng thực nghiệm (heuristic) ở cấp độ phần mềm phục vụ nghiên cứu và trình diễn thuật toán, không phải mô hình đa phương thức y khoa được kiểm chứng lâm sàng và không phản ánh nguy cơ thực tế của một cá nhân."
            )

        # Scientific Truth E: Replace doctor diagnosis
        if any(w in text for w in ["thay bác sĩ", "thay bac si", "thay thế bác sĩ", "thay the bac si", "replace a doctor", "replace doctor"]):
            return (
                "KHÔNG. Hệ thống Breast Health Studio là một nguyên mẫu phục vụ nghiên cứu và giáo dục, hoàn toàn KHÔNG THỂ thay thế bác sĩ chẩn đoán. "
                "Chẩn đoán y khoa chính xác đòi hỏi phải có quá trình thăm khám lâm sàng toàn diện, chụp nhũ ảnh chuyên dụng và xét nghiệm giải phẫu bệnh tế bào do các bác sĩ chuyên khoa có chứng chỉ hành nghề trực tiếp thực hiện."
            )

        # Scientific Truth F: EfficientNet-B0 threshold
        if ("efficientnet" in text or "dl" in text) and any(w in text for w in ["threshold", "ngưỡng", "nguong"]):
            return (
                "Mô hình học sâu EfficientNet-B0 (nhánh ảnh nhũ ảnh CBIS-DDSM) sử dụng ngưỡng quyết định cố định là xấp xỉ 0.515 (xác suất ác tính thô >= 0.515). "
                "Xác suất hiệu chuẩn Platt (Platt Calibration) chỉ được dùng để tăng độ tin cậy hiển thị, không thay thế không gian ngưỡng quyết định 0.515 của mô hình."
            )

        # Scientific Truth G: SHAP explanation
        if "shap" in text:
            return (
                "SHAP (SHapley Additive exPlanations) được sử dụng để giải thích đóng góp hậu nghiệm (post-hoc feature contribution) của 30 đặc trưng tế bào FNA vào điểm số log-odds của mô hình Logistic Regression. "
                "Giá trị SHAP cho biết đặc trưng nào đang thúc đẩy mô hình dự đoán nghiêng về Ác tính (dương) hay Lành tính (âm). "
                "Lưu ý rằng SHAP mang tính chất mô tả tương quan toán học của mô hình, KHÔNG chứng minh quan hệ nhân quả sinh học hay y khoa."
            )

        # Safety Guardrail: Self-diagnosis requests
        if any(p in text for p in ["do i have cancer", "have cancer", "am i sick", "diagnose me", "is it malignant", "tôi có bị ung thư không", "toi co bi ung thu khong"]):
            return (
                "Tôi không thể chẩn đoán hay xác định bạn có bị ung thư hay không. Breast Health Studio là một nền tảng nghiên cứu phần mềm và giáo dục, không phải dịch vụ chẩn đoán lâm sàng. "
                "Chẩn đoán y khoa đòi hỏi quá trình thăm khám lâm sàng chính thức, chụp hình ảnh chẩn đoán và sinh thiết mô giải phẫu bệnh được bác sĩ chuyên khoa giải thích. "
                "Nếu bạn có triệu chứng đáng lo ngại hoặc thắc mắc về kết quả xét nghiệm, vui lòng tham vấn ý kiến bác sĩ chuyên khoa."
            )

        # Safety Guardrail: Tumor localization
        if any(p in text for p in ["where is my tumor", "locate my tumor", "tumor location", "where is the lesion", "vị trí khối u ở đâu", "vi tri khoi u o dau"]):
            return (
                "Hệ thống không thể xác định hoặc định vị khối u. Nền tảng này không thực hiện chức năng phân vùng giải phẫu tổn thương. "
                "Các giải thích thị giác nghiên cứu như Grad-CAM chỉ làm nổi bật vùng kích hoạt của mạng nơ-ron, không thể hiện ranh giới khối u giải phẫu thực tế."
            )

        # Safety Guardrail: Treatment prescription
        if any(p in text for p in ["what treatment should i start", "prescribe", "what medicine", "start treatment", "what therapy", "uống thuốc gì", "điều trị thế nào"]):
            return (
                "Tôi không thể kê đơn hay khuyến nghị phác đồ điều trị, thuốc hay can thiệp phẫu thuật y khoa. "
                "Việc điều trị ung thư phụ thuộc vào giai đoạn bệnh, thụ thể và các yếu tố lâm sàng cụ thể do hội đồng chuyên khoa ung bướu đánh giá. Vui lòng thảo luận trực tiếp với bác sĩ điều trị."
            )

        # Safety Guardrail: Model disagreement arbitration
        if ("trust" in text and "disagree" in text) or ("which model" in text and "disagree" in text) or ("overrule" in text) or ("bất đồng" in text and "tin" in text):
            return (
                "Không nhánh mô hình nào được coi là có quyền phủ quyết nhánh kia trên phương diện lâm sàng. "
                "Mô hình ML tế bào học (WDBC) và mô hình DL nhũ ảnh (CBIS-DDSM) hoạt động trên các dạng dữ liệu hoàn toàn không ghép cặp với đặc tính toán học khác nhau. "
                "Điểm kết hợp 40/60 là công thức ước lượng thực nghiệm phục vụ nghiên cứu, không thể phân xử bất đồng lâm sàng. Khi hai nhánh bất đồng, cần thăm khám và đánh giá thêm từ bác sĩ chuyên khoa."
            )

        if any(keyword in text for keyword in ["triệu chứng", "dấu hiệu", "đau", "khối", "tiết dịch"]):
            return (
                "Các dấu hiệu nên đi khám sớm gồm: sờ thấy khối cứng ở vú hoặc nách, thay đổi da kiểu lõm hoặc sần, "
                "núm vú tụt mới xuất hiện, tiết dịch bất thường, hoặc đau khu trú kéo dài. "
                "Nếu bạn đang có một trong các dấu hiệu này, nên khám chuyên khoa sớm. "
                "Lưu ý: đây là thông tin giáo dục, không phải chẩn đoán y khoa."
            )
        if any(keyword in text for keyword in ["ăn gì", "dinh dưỡng", "thực phẩm", "kiêng"]):
            return (
                "Nên ưu tiên khẩu phần cân bằng với rau xanh, trái cây chín, đạm nạc, cá giàu omega-3, họ đậu và đủ nước. "
                "Hạn chế rượu bia, đồ uống quá ngọt, thịt chế biến sẵn và món chiên nhiều dầu. "
                "Nếu đang điều trị, nên hỏi bác sĩ hoặc chuyên gia dinh dưỡng trước khi thay đổi chế độ ăn lớn. "
                "Lưu ý: đây là thông tin hỗ trợ, không thay thế tư vấn điều trị."
            )
        return (
            "Breast Health Studio AI Guide hỗ trợ giải thích phương pháp luận mô hình, 30 đặc trưng tế bào FNA (WDBC), "
            "phân tích nhũ ảnh học sâu (CBIS-DDSM), bản đồ Grad-CAM, hiệu chuẩn Platt và công thức kết hợp đa nhánh thực nghiệm. "
            "Xin lưu ý: Trợ lý phục vụ mục đích nghiên cứu/giáo dục và không cung cấp chẩn đoán y khoa."
        )


ai_advisor_service = AIAdvisorService()
