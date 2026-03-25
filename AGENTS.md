# AGENTS.md

## Goal
Build a simple Windows desktop EXE photo viewer with local OCR.

## Product requirements
The app only needs these features:
- Image display
- Previous/next navigation within a selected folder
- Automatic OCR when an image is opened
- OCR overlay boxes on the image
- Text selection by OCR line
- Copy selected text
- Full text panel on the right

## Technical requirements
- Use Python
- Use PySide6 for the desktop UI
- Use PaddleOCR for local OCR
- Use PyInstaller for packaging to Windows EXE
- Keep everything local/offline as much as possible
- Do not use paid cloud OCR APIs
- Prefer a simple and maintainable architecture over advanced design
- Target Windows 11 first

## UX requirements
- Very simple UI for non-engineer users
- Main window with image viewer in the center
- Toolbar with: Open Folder, Previous, Next, Re-run OCR, Copy
- Right panel with:
  - full OCR text
  - OCR lines list
  - selected line text
  - copy buttons
- Show OCR bounding boxes as a light overlay
- Clicking an OCR box should select the corresponding text line
- Clicking a text line should highlight the corresponding OCR box

## Scope control
Do not add extra features unless necessary.
Do not add login, sync, database, cloud storage, or user accounts.
Do not add translation, search, QR reading, or advanced document parsing.
Do not over-engineer.

## Performance and packaging
- Cache OCR results per image while the app is running
- Support png, jpg, jpeg
- Package for Windows with PyInstaller
- Include a clear README with setup, run, and build instructions

## Deliverables
Create:
- source code
- requirements.txt
- README.md
- PyInstaller spec or build instructions
- a reasonable project structure