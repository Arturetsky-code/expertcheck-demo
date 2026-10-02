from core.ai_gateway import AIResult, GeminiProvider, GroqProvider


def test_gemini_vision_sends_inline_image_and_strict_schema():
    provider=GeminiProvider("key","gemini-test")
    captured={}
    def fake_post(url,headers,payload,timeout=45):
        captured.update({"url":url,"headers":headers,"payload":payload})
        return 200,{"candidates":[{"content":{"parts":[{"text":"{\"items\":[]}" }]}}]}
    provider._post=fake_post
    result=provider.generate_vision_structured(
        "check","QUJD","image/jpeg","RETURN JSON",
        json_schema={"type":"object","properties":{"items":{"type":"array"}},"required":["items"]},
    )
    assert result.ok is True
    parts=captured["payload"]["contents"][0]["parts"]
    assert parts[0]["text"]=="check"
    assert parts[1]["inlineData"]["mimeType"]=="image/jpeg"
    assert parts[1]["inlineData"]["data"]=="QUJD"
    assert captured["payload"]["generationConfig"]["responseMimeType"]=="application/json"


def test_groq_vision_selects_only_available_multimodal_model():
    provider=GroqProvider("key","openai/gpt-oss-120b")
    provider.available_models=lambda:(
        AIResult(True,"Groq",status_code=200),
        ["openai/gpt-oss-120b","meta-llama/llama-4-scout-17b-16e-instruct"],
    )
    captured={}
    def fake_post(url,headers,payload,timeout=45):
        captured["payload"]=payload
        return 200,{"choices":[{"message":{"content":"{\"items\":[]}"}}]}
    provider._post=fake_post
    result=provider.generate_vision("check","QUJD","image/png","RETURN JSON")
    assert result.ok is True
    assert result.model=="meta-llama/llama-4-scout-17b-16e-instruct"
    content=captured["payload"]["messages"][-1]["content"]
    assert content[0]=={"type":"text","text":"check"}
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,QUJD")


def test_groq_vision_fails_closed_without_multimodal_model():
    provider=GroqProvider("key","openai/gpt-oss-120b")
    provider.available_models=lambda:(
        AIResult(True,"Groq",status_code=200),
        ["openai/gpt-oss-120b","openai/gpt-oss-20b"],
    )
    result=provider.generate_vision("check","QUJD")
    assert result.ok is False
    assert result.status_code==412
    assert "мультимодальной" in result.error
