# Museum of Misplaced Meaning

**An imaginary contemporary art museum that takes everyday objects far too seriously.**

Describe one object from your pocket, bag, or desk. The app generates (1) a complete museum tombstone, (2) an 80–120-word theoretical interpretation, and (3) an exhibition photograph showing the same object installed as art. The label is displayed beside the image as in a physical gallery.

The generated artist, theorist and book are **fictional**; no real person is credited with the imagined works.

## Technology

- Python + Flask for the server, HTML/CSS/vanilla JavaScript for the responsive gallery.
- OpenAI text model (`gpt-5.4-mini` by default), with **structured output** parsed into a Pydantic `GalleryLabel`.
- OpenAI Images API (`gpt-image-2.5-flare` by default) returning `b64_json`, checked and converted to a `data:image/png;base64,...` URI.
- The API key is **never sent to the browser** or committed to Git; it resides in the server's environment.
- No user objects or images are stored in a database. Results disappear on refresh, but the displayed image can be saved.

> Updated for November 2026: OpenAI retired `gpt-image-1` on October 23, 2026. Do not copy old examples that use it. The configured model here is `gpt-image-2.5-flare`. Model availability, pricing and access depend on your API account.

## Run locally (Windows PowerShell)

1. Install Python 3.11 or newer.
2. Open PowerShell in the project root:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

3. Edit `.env` and replace `sk-your-key-here` with your own valid OpenAI API key. The OpenAI API requires separate API billing; ChatGPT subscriptions do not automatically cover it.
4. Run the local application:

   ```powershell
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.

**macOS/Linux**: replace the activation command with `source .venv/bin/activate` and `Copy-Item` with `cp`.

### Environment variables

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Required, server-side API secret |
| `TEXT_MODEL` | Default `gpt-5.4-mini` |
| `IMAGE_MODEL` | Default `gpt-image-2.5-flare` |
| `MAX_GENERATIONS_PER_HOUR` | Per-IP, per-server-instance limit, default `8` |
| `FLASK_DEBUG` | Set to `1` only during local development |

## User guide

1. Describe a **single** ordinary object (6–400 characters). Details like color, material, wear and use help make the eventual artwork accurate.
2. Or click one of the three example chips to fill the text area.
3. Click **Install in the Gallery**. The model first writes the formal label; only after the label is created does the image model receive a derived image prompt.
4. Wait for the image to finish. The exhibit appears with the museum tombstone and interpretation in the panel beside the image.
5. Click **Copy Label** to copy the complete tombstone + interpretation, or **Save Artwork** to download the PNG.
6. Enter another object to create a new acquisition. A page refresh resets the ephemeral gallery.

Image generation can take some time and **uses paid API credits**. If the API key is missing, the server returns a configuration message rather than exposing credentials.

## Prompt research: International Art English (IAE)

Alix Rule and David Levine's *International Art English* (Triple Canopy, 2012) examines a recognizable, sometimes exclusionary dialect in art-world press releases and exhibition texts. I exaggerate five features:

| IAE feature | Translation into an explicit prompt rule |
| --- | --- |
| **Abstract nominalization**: turning actions and relationships into nouns | Rule 2 requests *materiality, relationality, precarity* and similar abstract nouns; the paperclip no longer clips, it performs “containment.” |
| **Spatial and relational metaphors** | Rule 2 uses *site, threshold, liminal, between, within* to make a desk object resemble a philosophical installation. |
| **Paradox and productive contradictions** | Rule 2 asks for “paradoxical pairings” such as “a stable condition of perpetual movement.” |
| **Detached curatorial authority** | Rules 2 and 6 demand deadpan institutional language, passive voice, and no winks at the joke. |
| **Prestige through citations and genealogies** | Rule 4 requires exactly one completely invented theorist and an invented book cited in the extended label. |

The system prompt also defines **Rule 1 (physical fidelity), Rule 3 (complete museum metadata), Rule 5 (installation scale)**, for a total of six explicit curatorial rules. The most important constraint is that the physical object remains accurate. The mismatch between a rust spot and a dissertation-level theory is the artwork's central mechanism.

**Research source:** Rule, Alix, and David Levine. [“International Art English.” *Triple Canopy* (2012)](https://canopycanopycanopy.org/contents/international_art_english).

## How the image prompt is derived from the label

The generation pipeline is deliberate and **one-directional**:

```text
visitor's description
         │
         ▼
text model + six curatorial rules
         │
         ▼
structured GalleryLabel (tombstone, interpretation, setting)
         │
         ▼
build_image_prompt(label)  ← NEVER reads the original description
         │
         ▼
Images API (b64_json) → PNG data URI → gallery display
```

The image prompt includes the **generated** title, medium, dimensions, provenance, full extended text, and chosen setting (`white cube gallery`, `museum vitrine`, `spotlit plinth`, `biennale pavilion`). It makes the dimensions physically binding. For example, if the text model assigns a paperclip dimensions of `600 × 400 × 200 cm`, the image model is told to show a room-sized, recognizably paperclip-shaped installation with architectural clues for scale. If dimensions are variable, it should instead show a visible site-specific arrangement or repeated components. The prompt explicitly rejects replacing the original object with an unrelated metaphorical sculpture.

**Why chain instead of independently prompting both models?** Independent generation often produces a disconnect between the label and the image. Chaining gives the two artifacts a shared curatorial fiction, including scale, materials, and context. The text model makes the interpretation; the image model installs that interpretation as an exhibition photograph.

## Reflection: Why is a language model so fluent in this dialect?

A language model does not need to understand the social stakes of an exhibition to learn how art writing *sounds*. Its training encounters patterns of institutional language across descriptions, criticism, academic writing, promotional texts, and museum copy. The recognizably repeated structures—nominalizations, spatial metaphors, theoretical references and elaborate assertions of significance—can be imitated and recombined convincingly. This is especially revealing with ordinary objects: a bent paperclip can acquire an apparently prestigious conceptual framework almost instantly, even when nothing about the object has changed.

That fluency also makes me question what such language does in the real art world. Technical jargon can express genuine complexity, but it can also signal membership or authority while making the subject harder to see. The generated wall labels expose how quickly prestige can be manufactured through tone and invented citation. The machine's confidence is not evidence of expertise. In this project, I want the visitor to notice the gap between the physical object and its monumental explanation, and to ask who gets to decide when something counts as art.

## Test the project

Install the test dependencies and run:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

See also [TEST_REPORT.md](TEST_REPORT.md) for checks completed in this environment and the outstanding live QA checklist.

The tests cover: valid/invalid extended-label length and fictional citations, required prompt rules, an image prompt based on the label's dimensions rather than raw input, base64-to-PNG conversion, bad image data, form HTML, input validation, missing API keys, a fully mocked end-to-end `/api/generate` response, and safe error messages. Tests mock the API so they **do not incur fees**.

**Final manual QA with a real API key:** test a small paperclip, a monumental/variable-scale piece, a sock, and a receipt; confirm the title and image match, check mobile layout, verify copy/download, and review billing usage. This live check cannot be completed without valid API credentials.

## Deploy to Render

1. Create a **new public GitHub repository** (not the old class boilerplate repo). Push this project to it.
2. In [Render](https://dashboard.render.com/), choose **New → Web Service**, link your GitHub repository, and select Python. This project includes a `render.yaml` blueprint, or configure manually with:

   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 240`

3. In Render's **Environment** settings, add `OPENAI_API_KEY` as a secret. Optionally set `TEXT_MODEL`, `IMAGE_MODEL`, and `MAX_GENERATIONS_PER_HOUR`.
4. Deploy and test the public `.onrender.com` URL with one real object.
5. Submit **both** the live Render URL and the new public GitHub repository URL.

The included lightweight limiter is per-process and resets on restart; it is suitable only for a modest classroom demo. For a popular public app, use a persistent rate limiter (e.g., Redis), monitor usage, and set OpenAI billing limits. Keep the key secret. Render free-tier limits and availability may change.

### Preserve development history when publishing

If you received a project archive that **includes `.git`**, these staged local commits are already present. Extract the folder, open a terminal inside it, create a new *empty* public GitHub repository, then:

```bash
git log --oneline
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/museum-of-misplaced-meaning.git
git push -u origin main
```

Do not upload `.env` or paste the API key into GitHub. The included `.gitignore` excludes secrets.

## Sources and documentation

- Alix Rule & David Levine, [International Art English](https://canopycanopycanopy.org/contents/international_art_english), *Triple Canopy*.
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
- [OpenAI Images API](https://developers.openai.com/api/reference/resources/images/methods/generate).
- [Render: Deploy a Flask App](https://render.com/docs/deploy-flask).
- Original class [minimal Flask boilerplate](https://github.com/CART-ACT/minimal-flask-app/) (used as general architectural reference, not as the submission repository).
