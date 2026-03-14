"""Unified language constants for meetscribe.

Single source of truth for language names, section headers, PDF labels,
alignment model registry, and RTL detection.  Eliminates three duplicate
language-name dicts that were spread across transcribe.py, summarize.py,
and cli.py.
"""

from __future__ import annotations


# ─── Language names ─────────────────────────────────────────────────────────

LANG_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "tr": "Turkish",
    "fa": "Persian (Farsi)",
}
"""Map ISO 639-1 codes to human-readable language names."""


# ─── RTL detection ──────────────────────────────────────────────────────────

RTL_LANGUAGES: frozenset[str] = frozenset({"fa", "ar", "he", "ur"})
"""Language codes that use right-to-left script."""


def is_rtl(lang: str) -> bool:
    """Return True if *lang* uses a right-to-left script."""
    return lang in RTL_LANGUAGES


# ─── Section headers (for AI summary prompts) ──────────────────────────────

SECTION_HEADERS: dict[str, dict[str, str]] = {
    "en": {
        "overview": "Meeting Overview",
        "topics": "Key Topics Discussed",
        "actions": "Action Items",
        "decisions": "Decisions Made",
        "questions": "Open Questions / Follow-ups",
        "none_stated": "None explicitly stated",
    },
    "de": {
        "overview": "Besprechungsübersicht",
        "topics": "Besprochene Hauptthemen",
        "actions": "Aufgaben",
        "decisions": "Getroffene Entscheidungen",
        "questions": "Offene Fragen / Nachverfolgung",
        "none_stated": "Keine ausdrücklich genannt",
    },
    "fr": {
        "overview": "Aperçu de la réunion",
        "topics": "Sujets clés abordés",
        "actions": "Points d'action",
        "decisions": "Décisions prises",
        "questions": "Questions ouvertes / Suivis",
        "none_stated": "Aucun mentionné explicitement",
    },
    "es": {
        "overview": "Resumen de la reunión",
        "topics": "Temas clave discutidos",
        "actions": "Puntos de acción",
        "decisions": "Decisiones tomadas",
        "questions": "Preguntas abiertas / Seguimientos",
        "none_stated": "Ninguno mencionado explícitamente",
    },
    "tr": {
        "overview": "Toplantı Özeti",
        "topics": "Tartışılan Ana Konular",
        "actions": "Eylem Maddeleri",
        "decisions": "Alınan Kararlar",
        "questions": "Açık Sorular / Takip Edilecekler",
        "none_stated": "Açıkça belirtilmedi",
    },
    "fa": {
        "overview": "خلاصه جلسه",
        "topics": "موضوعات کلیدی مورد بحث",
        "actions": "اقدامات لازم",
        "decisions": "تصمیمات اتخاذ شده",
        "questions": "سؤالات باز / پیگیری‌ها",
        "none_stated": "هیچ موردی صریحاً ذکر نشده است",
    },
}


# ─── PDF section labels ────────────────────────────────────────────────────

# ─── Meeting type prompts (appended to base system prompt) ────────────────

MEETING_TYPE_PROMPTS: dict[str, str] = {
    "general": "",
    "class": (
        "This is a yoga, breathwork, or wellness class recording. Focus on: "
        "techniques and sequences taught, verbal cues and instructions given by "
        "the instructor, any modifications or variations offered, student questions "
        "and the instructor's responses, and the overall flow of the session. "
        "Use wellness-appropriate language."
    ),
    "business": (
        "This is a business meeting. Focus on: concrete decisions made with owners "
        "and deadlines, action items assigned to specific people, pricing discussions "
        "and financial figures mentioned, project timelines and milestones, and any "
        "follow-up meetings or deliverables agreed upon. Be precise with numbers "
        "and commitments."
    ),
    "board": (
        "This is a nonprofit board meeting. Focus on: motions made and how they "
        "were voted on (passed/failed/tabled), financial reports and budget items "
        "discussed, committee reports and updates, any bylaws or policy changes, "
        "and items requiring follow-up before the next meeting. Use formal "
        "parliamentary language where appropriate."
    ),
    "training": (
        "This is a professional training or continuing education session. Focus on: "
        "key concepts and frameworks taught, techniques or methodologies demonstrated, "
        "CE-relevant takeaways and learning objectives covered, practical exercises "
        "or case studies discussed, and any resources or references mentioned. "
        "Highlight material that would be relevant for CE credit documentation."
    ),
}
"""Meeting-type-specific prompt suffixes for context-aware summaries."""


# ─── PDF section labels ────────────────────────────────────────────────────

PDF_SECTIONS: dict[str, dict[str, str]] = {
    "en": {"summary": "AI Meeting Summary", "transcript": "Full Transcript"},
    "de": {"summary": "KI-Besprechungszusammenfassung", "transcript": "Vollständiges Transkript"},
    "fr": {"summary": "Résumé de réunion (IA)", "transcript": "Transcription complète"},
    "es": {"summary": "Resumen de reunión (IA)", "transcript": "Transcripción completa"},
    "tr": {"summary": "Yapay Zeka Toplantı Özeti", "transcript": "Tam Transkript"},
    "fa": {"summary": "خلاصه جلسه (هوش مصنوعی)", "transcript": "رونوشت کامل"},
}
