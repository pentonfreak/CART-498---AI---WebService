"""Pure logic tests: these never call the real API or charge a cent."""

import base64
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from museum import GalleryLabel, SYSTEM_PROMPT, build_image_prompt, generate_exhibition_image, generate_wall_label


LABEL_TEXT = (
    "The bent paperclip remains attached to a condition of endless administrative waiting. "
    "Its narrow metal body and visible rust spot convert modest office labor into a site "
    "of precarious suspension. In the account of fictional theorist Mara Senn, writing in "
    "her invented book The Folded Threshold, the gesture of holding is already a form of "
    "release. Here the clip's small curve refuses both stability and escape. The work "
    "invites us to inhabit the interval between a document and its possibility of "
    "disappearance. What seems disposable instead performs an unusually intimate "
    "archive of unclaimed attention."
)


def make_label(**overrides):
    data = dict(
        artist="Oren Vale",
        artist_bio="b. 1996; lives and works between the paper tray and the cloud",
        title="The Administrative Interval",
        year="2026",
        medium="Steel, oxidation, deferred attention",
        dimensions="600 × 400 × 200 cm",
        provenance="Desk drawer, 2026; acquired from an anonymous office worker",
        credit_line="Gift of the last stapler",
        extended_label=LABEL_TEXT,
        theorist_name="Mara Senn",
        theorist_book="The Folded Threshold",
        exhibition_setting="white cube gallery",
    )
    data.update(overrides)
    return GalleryLabel(**data)


def test_valid_label_and_word_count():
    label = make_label()
    assert 80 <= len(label.extended_label.split()) <= 120
    assert label.exhibition_setting == "white cube gallery"


def test_rejects_missing_theorist_or_book():
    with pytest.raises(ValidationError):
        make_label(theorist_name="Someone Else")
    with pytest.raises(ValidationError):
        make_label(theorist_book="The Unwritten Book")


def test_rejects_short_label():
    with pytest.raises(ValidationError):
        make_label(extended_label="An extremely brief work by Mara Senn in The Folded Threshold.")


def test_three_or_more_prompt_rules_are_explicit():
    assert "1. PHYSICAL FIDELITY" in SYSTEM_PROMPT
    assert "2. INSTITUTIONAL INFLATION" in SYSTEM_PROMPT
    assert "3. FORMAL LABEL" in SYSTEM_PROMPT
    assert "4. THEORY AS FICTION" in SYSTEM_PROMPT


def test_image_prompt_chains_only_label_not_user_description():
    label = make_label()
    prompt = build_image_prompt(label)
    assert "600 × 400 × 200 cm" in prompt
    assert "Steel, oxidation" in prompt
    assert label.extended_label in prompt
    assert "white cube gallery" in prompt
    assert "DIMENSIONS" in prompt
    assert "tiny purple widget from my backpack" not in prompt


def test_gpt_image_base64_decoding_to_data_uri():
    # Minimal valid PNG header + payload is enough for a mocked response.
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake-image-bytes"
    b64 = base64.b64encode(png_bytes).decode("ascii")
    calls = []

    class MockImages:
        def generate(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(b64_json=b64)])

    client = SimpleNamespace(images=MockImages())
    uri = generate_exhibition_image(client, make_label())
    assert uri.startswith("data:image/png;base64,")
    assert base64.b64decode(uri.split(",", 1)[1]) == png_bytes
    assert calls[0]["model"] == "gpt-image-2.5-flare"
    assert "600 × 400 × 200 cm" in calls[0]["prompt"]
    assert calls[0]["output_format"] == "png"


def test_rejects_corrupt_image():
    client = SimpleNamespace(images=SimpleNamespace(generate=lambda **kw: SimpleNamespace(
        data=[SimpleNamespace(b64_json=base64.b64encode(b"not-a-png").decode())]
    )))
    with pytest.raises(ValueError, match="PNG"):
        generate_exhibition_image(client, make_label())


def test_generate_label_using_fake_openai_parse():
    calls = []
    label = make_label()

    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=label, refusal=None))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    output = generate_wall_label(client, "A bent paperclip with rust")
    assert output.artist == "Oren Vale"
    assert calls[0]["response_format"] is GalleryLabel
    assert "A bent paperclip with rust" in calls[0]["messages"][1]["content"]


def test_generate_label_retries_after_validation_failure():
    calls = []
    label = make_label()

    def parse(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            # A malformed model response can fail Pydantic validation inside
            # the OpenAI SDK before a ChatCompletion is returned.
            make_label(extended_label="Too short: Mara Senn, The Folded Threshold.")
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=label, refusal=None))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    result = generate_wall_label(client, "A bent rusty paperclip")
    assert result.title == label.title
    assert len(calls) == 2
    assert "80-120 WORDS" in calls[1]["messages"][1]["content"]
