"""WhatsApp media understanding (documents, images, and audio first).

Scope: download media that wa-enggine already fetched, parse documents
(pdf/docx/txt/md/csv/json/xlsx/pptx) and images (OCR) into text, and let the
agent answer from the content. Audio is now supported through transcription
(``audio_transcriber.transcribe_audio``). Video understanding remains out of
scope for this slice (see services/ai/docs/WA_AI_SECOND_BRAIN_AUDIT.md).
"""
