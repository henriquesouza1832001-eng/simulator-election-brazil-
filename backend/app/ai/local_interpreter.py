"""Small, auditable text classifiers trained from player-confirmed labels only.

Candidate models are evaluated offline. This module is deliberately not called
by the live interpretation path yet.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any


ALGORITHM = "multinomial_naive_bayes_words_and_bigrams_v1"
STOP_WORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "entre", "essa", "esse", "esta", "este", "na", "nas", "no",
    "nos", "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por",
    "que", "um", "uma", "umas", "uns", "vai", "vamos",
}
TOKEN_PATTERN = re.compile(r"[a-z]{3,}")


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    words = [word for word in TOKEN_PATTERN.findall(ascii_text) if word not in STOP_WORDS]
    bigrams = [f"{left}__{right}" for left, right in zip(words, words[1:])]
    return words + bigrams


def fit_naive_bayes(samples: list[dict[str, str]], alpha: float = 1.0,
                    max_features: int = 3000) -> dict[str, Any]:
    if not samples:
        raise ValueError("São necessários exemplos rotulados para treinar o classificador.")
    tokenized = [(tokenize(row["text"]), row["label"]) for row in samples]
    global_counts = Counter(token for tokens, _ in tokenized for token in tokens)
    vocabulary = [token for token, _ in global_counts.most_common(max_features)]
    vocabulary_set = set(vocabulary)
    classes: dict[str, dict[str, Any]] = {}
    for label in sorted({row["label"] for row in samples}):
        rows = [(tokens, target) for tokens, target in tokenized if target == label]
        counts = Counter(token for tokens, _ in rows for token in tokens if token in vocabulary_set)
        classes[label] = {
            "documents": len(rows),
            "token_total": sum(counts.values()),
            "token_counts": dict(sorted(counts.items())),
        }
    return {
        "algorithm": ALGORITHM,
        "alpha": alpha,
        "documents": len(samples),
        "vocabulary": vocabulary,
        "classes": classes,
    }


def predict(model: dict[str, Any], text: str) -> dict[str, Any]:
    classes = model.get("classes", {})
    vocabulary = set(model.get("vocabulary", []))
    if not classes or not vocabulary:
        raise ValueError("O modelo não contém classes e vocabulário.")
    tokens = [token for token in tokenize(text) if token in vocabulary]
    total_documents = max(1, int(model.get("documents", 0)))
    alpha = float(model.get("alpha", 1.0))
    vocab_size = max(1, len(vocabulary))
    scores: dict[str, float] = {}
    for label, details in classes.items():
        documents = max(1, int(details.get("documents", 0)))
        token_total = int(details.get("token_total", 0))
        counts = details.get("token_counts", {})
        score = math.log(documents / total_documents)
        denominator = token_total + alpha * vocab_size
        score += sum(
            math.log((int(counts.get(token, 0)) + alpha) / denominator)
            for token in tokens
        )
        scores[label] = score
    maximum = max(scores.values())
    normalizer = sum(math.exp(score - maximum) for score in scores.values())
    probabilities = {label: math.exp(score - maximum) / normalizer for label, score in scores.items()}
    label = max(scores, key=lambda key: (scores[key], key))
    return {"label": label, "confidence": probabilities[label], "matched_tokens": len(tokens)}


def evaluate_field(samples: list[dict[str, str]], field: str, *,
                   min_per_class: int = 5, min_accuracy: float = 0.75,
                   seed: int = 41) -> dict[str, Any]:
    """Run a deterministic, class-stratified holdout before fitting a candidate."""
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in samples:
        label = row.get("labels", {}).get(field)
        if isinstance(label, str) and row.get("text", "").strip():
            grouped[label].append({"text": row["text"], "label": label})
    eligible = {label: rows for label, rows in grouped.items() if len(rows) >= min_per_class}
    excluded = {label: len(rows) for label, rows in grouped.items() if len(rows) < min_per_class}
    if len(eligible) < 2:
        return {
            "ready": False, "accuracy": None, "examples": sum(map(len, eligible.values())),
            "classes": {label: len(rows) for label, rows in grouped.items()},
            "excluded_classes": excluded, "reason": "São necessárias duas classes com pelo menos cinco correções cada.",
            "model": None,
        }

    import random
    rng = random.Random(seed)
    train_rows: list[dict[str, str]] = []
    test_rows: list[dict[str, str]] = []
    for label in sorted(eligible):
        rows = list(eligible[label])
        rng.shuffle(rows)
        test_count = max(1, round(len(rows) * 0.2))
        test_count = min(test_count, len(rows) - 2)
        test_rows.extend(rows[:test_count])
        train_rows.extend(rows[test_count:])

    validation_model = fit_naive_bayes(train_rows)
    correct_by_class: Counter[str] = Counter()
    total_by_class: Counter[str] = Counter()
    for row in test_rows:
        predicted = predict(validation_model, row["text"])["label"]
        total_by_class[row["label"]] += 1
        if predicted == row["label"]:
            correct_by_class[row["label"]] += 1
    correct = sum(correct_by_class.values())
    accuracy = correct / max(1, len(test_rows))
    qualified = accuracy >= min_accuracy
    candidate = fit_naive_bayes([row for label in sorted(eligible) for row in eligible[label]]) if qualified else None
    return {
        "ready": qualified,
        "accuracy": round(accuracy, 4),
        "minimum_accuracy": min_accuracy,
        "examples": sum(map(len, eligible.values())),
        "training_examples": len(train_rows),
        "held_out_examples": len(test_rows),
        "classes": {label: len(rows) for label, rows in eligible.items()},
        "excluded_classes": excluded,
        "per_class_accuracy": {
            label: round(correct_by_class[label] / count, 4)
            for label, count in sorted(total_by_class.items())
        },
        "reason": None if qualified else "A acurácia de validação não atingiu o limite; o artefato não foi atualizado.",
        "model": candidate,
    }
