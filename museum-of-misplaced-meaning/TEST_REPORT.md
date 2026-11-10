# Validation report

## Automated checks completed in the project-preparation environment

- `pytest -q tests/test_museum.py` — **9 passed**.
- `python -m compileall -q .` — passed (Python syntax compiles).
- `node --check static/app.js` — passed (JavaScript syntax valid).
- The text-generation and Images API calls are represented by mocks in the unit tests; no real API request or payment was made.

## Checks to perform after installing dependencies and adding your API key

- `pip install -r requirements-dev.txt`
- `pytest -q` — also runs Flask route tests under `tests/test_app.py`.
- `python app.py` — verify the page opens at `http://127.0.0.1:5000`.
- With an API key, submit at least three distinct objects: a normal-sized item, a monumental item, and a variable-scale installation. Verify dimensions, accuracy, and a visibly matching exhibition image.
- Verify responsive layout and the Copy Label / Save Artwork buttons in a browser.
- Verify the same end-to-end behavior on the deployed Render URL.

**Reason for the gap:** Flask and Gunicorn were not preinstalled here, and installing them was blocked by the isolated environment's unavailable package network. The full Flask test suite and real API calls have therefore **not** been run here. Passing mocked unit tests does not guarantee a live OpenAI account will accept every request or that image generation will accurately follow each prompt. Document these outcomes after your own live testing before submission.
