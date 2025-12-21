"""Content-based title generation for meeting transcriptions."""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional


STOP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "this", "that",
    "these", "those", "what", "which", "who", "whom", "whose", "where",
    "when", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "also", "now", "here", "there",
    "then", "once", "if", "because", "as", "until", "while", "although",
    "though", "after", "before", "since", "unless", "about", "into",
    "through", "during", "above", "below", "between", "under", "again",
    "further", "then", "once", "yeah", "yes", "no", "okay", "ok", "um",
    "uh", "like", "know", "think", "going", "want", "got", "get", "see",
    "look", "come", "go", "make", "take", "give", "say", "said", "tell",
    "told", "ask", "asked", "let", "well", "right", "good", "really",
    "actually", "basically", "literally", "kind", "sort", "thing", "things",
])

MEETING_KEYWORDS = frozenset([
    "meeting", "discussion", "review", "planning", "standup", "sync",
    "kickoff", "retrospective", "brainstorm", "interview", "onboarding",
    "training", "presentation", "demo", "update", "status", "quarterly",
    "weekly", "monthly", "annual", "budget", "roadmap", "strategy",
    "project", "product", "team", "client", "customer", "sales", "marketing",
])


def extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(filtered)
    return [word for word, _ in word_counts.most_common(max_keywords)]


def detect_meeting_type(text: str) -> Optional[str]:
    text_lower = text.lower()
    for keyword in MEETING_KEYWORDS:
        if keyword in text_lower:
            return keyword.title()
    return None


def generate_title(
    segments_text: str,
    fallback: str = "Meeting Transcript",
    max_words: int = 5,
) -> str:
    if not segments_text or len(segments_text.strip()) < 50:
        return fallback

    first_chunk = segments_text[:2000]

    meeting_type = detect_meeting_type(first_chunk)
    keywords = extract_keywords(first_chunk, max_keywords=max_words)

    if meeting_type:
        other_keywords = [k for k in keywords if k.lower() != meeting_type.lower()]
        if other_keywords:
            title_words = [meeting_type] + [k.title() for k in other_keywords[:max_words - 1]]
        else:
            title_words = [meeting_type]
    elif keywords:
        title_words = [k.title() for k in keywords]
    else:
        return fallback

    return " ".join(title_words)


def generate_title_from_segments(
    segments: list,
    fallback: str = "Meeting Transcript",
) -> str:
    text_parts = []
    for seg in segments:
        if hasattr(seg, "text"):
            text_parts.append(seg.text)
        elif isinstance(seg, dict) and "text" in seg:
            text_parts.append(seg["text"])

    full_text = " ".join(text_parts)
    return generate_title(full_text, fallback=fallback)
