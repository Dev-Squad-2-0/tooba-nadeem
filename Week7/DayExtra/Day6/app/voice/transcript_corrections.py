"""
transcript_corrections.py
---------------------------

Small, explicit fixup pass for known ASR mis-transcriptions of
domain-specific terms (mainly short acronyms like "DHA" that Deepgram's
acoustic model struggles with even with Keyterm Prompting enabled -- see
app/voice/stt_deepgram.py's REAL_ESTATE_KEYTERMS comment for context).

Deliberately NOT trying to be a general spell-checker -- just a small,
reviewable list of observed bad transcriptions -> correct terms, applied
as a literal substring pass. Extend this list as you observe more
mis-transcriptions during testing.
"""

import re

# (bad transcription seen in testing, correct term)
# Add entries as new mis-transcriptions are observed -- keep this list
# short and evidence-based, not speculative.
KNOWN_CORRECTIONS: list[tuple[str, str]] = [
    ("ڈیت", "DHA"),
    ("ڈیا", "DHA"),
    ("दिएथ", "DHA"),
    # "Tooba" (طوبیٰ) -- Deepgram commonly mis-transcribes this Urdu name.
    # Confirmed variants based on acoustic similarity; extend as new ones surface.
    ("Tuba", "Tooba"),
    ("Toba", "Tooba"),
    ("Toba", "Tooba"),
    ("Tuba", "Tooba"),
    ("Tauba", "Tooba"),
    ("Touba", "Tooba"),
    ("طوبا", "Tooba"),
    ("طوبیٰ", "Tooba"),
]


def apply_corrections(transcript: str) -> str:
    corrected = transcript
    for wrong, right in KNOWN_CORRECTIONS:
        corrected = re.sub(re.escape(wrong), right, corrected)
    return corrected