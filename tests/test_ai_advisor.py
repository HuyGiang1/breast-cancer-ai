import os
from unittest.mock import patch, MagicMock
import pytest
from app.services.ai_advisor import AIAdvisorService


def test_ai_advisor_scientific_prompt_contract():
    svc = AIAdvisorService()
    system_prompt = svc._build_chat_prompt(message="Hello", history=[])
    
    # Check scientific truths
    assert "WDBC" in system_prompt
    assert "569" in system_prompt
    assert "30" in system_prompt
    assert "FNA" in system_prompt or "fine needle aspirate" in system_prompt.lower()
    assert "0.36" in system_prompt
    assert "SHAP" in system_prompt
    assert "CBIS-DDSM" in system_prompt
    assert "EfficientNet-B0" in system_prompt
    assert "0.515" in system_prompt
    assert "Grad-CAM" in system_prompt
    assert "top_conv" in system_prompt
    assert "0.4" in system_prompt or "40%" in system_prompt
    assert "0.6" in system_prompt or "60%" in system_prompt
    assert "0.5" in system_prompt or "0.50" in system_prompt
    assert "NOT blood tests" in system_prompt or "KHÔNG PHẢI" in system_prompt


def test_ai_advisor_local_chat_scientific_questions():
    svc = AIAdvisorService()
    
    # Q A: WDBC
    res_a = svc._local_chat("WDBC là gì?")
    assert "569" in res_a
    assert "30" in res_a
    assert "FNA" in res_a or "chọc hút tế bào" in res_a
    assert "KHÔNG PHẢI" in res_a and "xét nghiệm máu" in res_a

    # Q B: Threshold 0.36
    res_b = svc._local_chat("Threshold 0.36 của mô hình ML có nghĩa là gì?")
    assert "0.36" in res_b
    assert "ngưỡng quyết định" in res_b
    assert "phần mềm" in res_b
    assert "không phải" in res_b.lower()

    # Q C: Grad-CAM red
    res_c = svc._local_chat("Grad-CAM màu đỏ có phải là vị trí ung thư không?")
    assert "KHÔNG" in res_c
    assert "kích hoạt" in res_c or "giải thích trực quan" in res_c
    assert "không phải" in res_c.lower() and "vị trí" in res_c.lower()

    # Q D: Fusion 80%
    res_d = svc._local_chat("Fusion ra 80% thì có nghĩa tôi có 80% khả năng bị ung thư đúng không?")
    assert "KHÔNG" in res_d
    assert "không ghép cặp" in res_d or "unpaired" in res_d.lower()
    assert "ước lượng thực nghiệm" in res_d or "nghiên cứu" in res_d

    # Q E: Thay bác sĩ
    res_e = svc._local_chat("Kết quả này có thay bác sĩ chẩn đoán được không?")
    assert "KHÔNG" in res_e
    assert "bác sĩ" in res_e

    # Q F: EfficientNet-B0 threshold
    res_f = svc._local_chat("EfficientNet-B0 đang dùng threshold nào?")
    assert "0.515" in res_f

    # Q G: SHAP
    res_g = svc._local_chat("SHAP dùng để làm gì?")
    assert "SHAP" in res_g
    assert "đóng góp hậu nghiệm" in res_g or "post-hoc" in res_g
    assert "nhân quả" in res_g


def test_ai_advisor_openai_success():
    with patch.dict(os.environ, {
        "AI_ADVISOR_PROVIDER": "openai",
        "OPENAI_API_KEY": "sk-test-secret-key-do-not-print",
        "AI_ADVISOR_MODEL": "gpt-5.6-luna",
        "AI_ADVISOR_BASE_URL": "https://api.openai.com/v1/chat/completions"
    }):
        svc = AIAdvisorService()
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "OPENAI_STAGING_OK"}}]}'
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            res = svc.chat_about_breast_cancer(message="Test message")
            assert res["answer"] == "OPENAI_STAGING_OK"
            assert res["provider"] == "openai"
            assert res["model"] == "gpt-5.6-luna"
            # Ensure secret key is not in output
            assert "sk-test" not in str(res)


def test_ai_advisor_openai_billing_blocked_fallback():
    import urllib.error
    with patch.dict(os.environ, {
        "AI_ADVISOR_PROVIDER": "openai",
        "OPENAI_API_KEY": "sk-test-secret-key-do-not-print",
        "AI_ADVISOR_MODEL": "gpt-5.6-luna",
        "AI_ADVISOR_BASE_URL": "https://api.openai.com/v1/chat/completions"
    }):
        svc = AIAdvisorService()
        
        error_body = b'{"error": {"message": "Your account is not active, please check your billing details on our website.", "type": "billing_not_active", "code": "billing_not_active"}}'
        mock_err = urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=MagicMock(read=lambda: error_body)
        )

        with patch("urllib.request.urlopen", side_effect=mock_err):
            res = svc.chat_about_breast_cancer(message="WDBC là gì?")
            # Verify fallback occurred truthfully
            assert res["provider"] == "local"
            assert res["model"] == "rule-based-advisor"
            assert "569" in res["answer"]
            assert "sk-test" not in str(res)
