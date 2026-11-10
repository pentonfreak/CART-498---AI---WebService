"""Flask integration tests use monkeypatch, not paid OpenAI requests."""

import app as app_module
from test_museum import make_label


def client(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_home_and_health(monkeypatch):
    web = client(monkeypatch)
    assert web.get("/").status_code == 200
    html = web.get("/").get_data(as_text=True)
    assert "Museum of Misplaced Meaning" in html
    assert 'id="object-description"' in html
    assert 'id="actual-label"' in html
    assert web.get("/health").json == {"status": "ok"}


def test_validation_rejects_empty_bad_and_oversized_descriptions(monkeypatch):
    web = client(monkeypatch)
    assert web.post("/api/generate", data="abc", headers={"Content-Type": "text/plain"}).status_code == 415
    assert web.post("/api/generate", json={"object_description": "x"}).status_code == 400
    assert web.post("/api/generate", json={"object_description": "x" * 401}).status_code == 400
    assert web.post("/api/generate", json={"object_description": 123}).status_code == 400
    assert web.post("/api/generate", data="{" , content_type="application/json").status_code == 400


def test_missing_server_api_key(monkeypatch):
    web = client(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY")
    response = web.post("/api/generate", json={"object_description": "A chipped ceramic mug"})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json["error"]


def test_full_mocked_exhibit_from_post(monkeypatch):
    web = client(monkeypatch)
    calls = {}

    def fake_wall_label(client, description, model):
        calls["description"] = description
        calls["text_model"] = model
        return make_label()

    def fake_image(client, label, model):
        calls["image_received_label"] = label
        calls["image_model"] = model
        return "data:image/png;base64,iVBORw0KGgo="

    monkeypatch.setattr(app_module, "generate_wall_label", fake_wall_label)
    monkeypatch.setattr(app_module, "generate_exhibition_image", fake_image)
    response = web.post("/api/generate", json={"object_description": " A bent paperclip with rust "})
    assert response.status_code == 200
    assert response.json["label"]["artist"] == "Oren Vale"
    assert response.json["image"].startswith("data:image/png;base64,")
    assert calls["description"] == "A bent paperclip with rust"
    assert calls["image_received_label"].title == "The Administrative Interval"
    assert "OPENAI_API_KEY" not in response.get_data(as_text=True)


def test_internal_errors_do_not_leak_secrets(monkeypatch):
    web = client(monkeypatch)
    def broken(*args):
        raise ValueError("this is a secret provider diagnostic")
    monkeypatch.setattr(app_module, "generate_wall_label", broken)
    response = web.post("/api/generate", json={"object_description": "A chipped ceramic mug"})
    assert response.status_code == 502
    assert "secret provider diagnostic" not in response.get_data(as_text=True)
