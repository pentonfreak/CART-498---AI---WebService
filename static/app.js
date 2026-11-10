'use strict';

const form = document.getElementById('curate-form');
const descriptionInput = document.getElementById('object-description');
const charCount = document.getElementById('char-count');
const submitButton = document.getElementById('submit-button');
const buttonText = document.getElementById('button-text');
const statusMessage = document.getElementById('status-message');
const loadingOverlay = document.getElementById('loading-overlay');
const emptyStage = document.getElementById('empty-stage');
const emptyLabel = document.getElementById('empty-label');
const actualLabel = document.getElementById('actual-label');
const image = document.getElementById('artwork-image');
const accessionNumber = document.getElementById('accession-number');
let currentImage = null;
let currentLabel = null;
let acquisitions = 0;

function updateCount() {
  charCount.textContent = `${descriptionInput.value.length} / 400`;
}

function status(text, isError = false) {
  statusMessage.textContent = text;
  statusMessage.classList.toggle('error', isError);
}

function setBusy(busy) {
  submitButton.disabled = busy;
  descriptionInput.disabled = busy;
  buttonText.textContent = busy ? 'CURATING, PLEASE WAIT…' : 'INSTALL IN THE GALLERY';
  loadingOverlay.hidden = !busy;
  document.querySelectorAll('.example-chip').forEach((chip) => { chip.disabled = busy; });
  form.setAttribute('aria-busy', String(busy));
}

function text(id, value) {
  document.getElementById(id).textContent = value || '—';
}

function renderExhibit(result) {
  const label = result.label;
  currentLabel = label;
  currentImage = result.image;

  text('work-title', label.title);
  text('work-year', label.year);
  text('artist-name', label.artist);
  text('artist-bio', label.artist_bio);
  text('medium', label.medium);
  text('dimensions', label.dimensions);
  text('provenance', label.provenance);
  text('credit-line', label.credit_line);
  text('extended-label', label.extended_label);

  image.src = result.image;
  image.alt = `Exhibition photograph of ${label.title}, displayed in a ${label.exhibition_setting}`;
  image.hidden = false;
  emptyStage.hidden = true;
  emptyLabel.hidden = true;
  actualLabel.hidden = false;
  acquisitions += 1;
  accessionNumber.textContent = String(acquisitions).padStart(4, '0');
  document.getElementById('gallery-state').textContent = 'WORK ACQUIRED / ON DISPLAY';
  document.getElementById('image-state').textContent = 'INSTALLATION PHOTOGRAPH';
  document.getElementById('gallery').scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
}

function fullLabel(label) {
  return `${label.artist}\n${label.artist_bio}\n${label.title}, ${label.year}\nMedium: ${label.medium}\nDimensions: ${label.dimensions}\nProvenance: ${label.provenance}\nCredit line: ${label.credit_line}\n\n${label.extended_label}`;
}

descriptionInput.addEventListener('input', updateCount);
document.querySelectorAll('.example-chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    descriptionInput.value = chip.dataset.example;
    updateCount();
    descriptionInput.focus();
    status('');
  });
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const objectDescription = descriptionInput.value.trim();
  if (objectDescription.length < 6 || objectDescription.length > 400) {
    status('Please describe one object in 6–400 characters.', true);
    descriptionInput.focus();
    return;
  }

  setBusy(true);
  status('The curator is considering your object. This may take a little while.');
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({object_description: objectDescription}),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'The acquisition could not be completed.');
    }
    if (!data.label || !data.image || !data.image.startsWith('data:image/png;base64,')) {
      throw new Error('The curator returned an incomplete exhibition.');
    }
    renderExhibit(data);
    status('Acquired. Your object is now officially overinterpreted.');
  } catch (error) {
    status(error.message || 'Something went wrong. Please try again.', true);
  } finally {
    setBusy(false);
  }
});

document.getElementById('copy-label').addEventListener('click', async () => {
  if (!currentLabel) return;
  try {
    await navigator.clipboard.writeText(fullLabel(currentLabel));
    status('Museum label copied to the clipboard.');
  } catch {
    status('Copy is unavailable in this browser. Select the label text to copy it.', true);
  }
});

document.getElementById('download-image').addEventListener('click', () => {
  if (!currentImage || !currentLabel) return;
  const anchor = document.createElement('a');
  anchor.href = currentImage;
  const safeTitle = currentLabel.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'museum-artwork';
  anchor.download = `${safeTitle}.png`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
});

updateCount();
