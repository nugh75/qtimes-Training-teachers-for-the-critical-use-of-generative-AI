#!/usr/bin/env python3
from __future__ import annotations

from ai_usage_qwen_common import (
    INDIVIDUALIZATION_STRATEGIES,
    LABELS_DIR,
    TEACHER_GROUPS,
    AnalysisConfig,
    run,
)


CONFIG = AnalysisConfig(
    name="teaching-individualization",
    logger_name="teaching_individualization_qwen",
    schema_version="teaching_individualization.v1",
    default_output_dir=LABELS_DIR / "ollama-qwen3-5-9b-teaching-individualization",
    description="Analisi qualitativa dell'individualizzazione dell'insegnamento con IA, solo insegnanti.",
    no_item_status="no_individualization_item",
    question_needles=(
        "utilizzi l intelligenza artificiale per individualizzare l insegnamento",
    ),
    allowed_groups=TEACHER_GROUPS,
    system_prompt="""Sei un analista qualitativo di pratiche didattiche.
Analizza esclusivamente la risposta del partecipante.

L'individualizzazione riguarda strategie per portare tutti gli studenti al raggiungimento
delle competenze fondamentali comuni, tramite diversificazione di percorsi, livelli,
scaffolding, recupero, semplificazione o feedback mirato. Non confonderla con la sola
personalizzazione orientata a interessi e talenti individuali.
Restituisci solo JSON valido.
""",
    task_prompt=(
        "Classifica come l'insegnante dichiara di usare l'IA per individualizzare "
        "l'insegnamento. Se non descrive una pratica, segnala practice_present=false."
    ),
    output_example="""{
  "items": [
    {
      "index": 3,
      "practice_present": true,
      "strategies": ["livelli_difficolta", "scaffolding_guidato"],
      "target": "sottogruppo",
      "ai_role": "suggerimento_strategie",
      "evidence": "preparo attività specifiche",
      "confidence": 0.78,
      "reason": "La risposta rimanda ad attività differenziate per supportare il percorso didattico."
    }
  ]
}""",
    allowed_values_text=(
        f"- strategies: {' | '.join(INDIVIDUALIZATION_STRATEGIES)};\n"
        "- target: singolo_studente | gruppo_classe | sottogruppo | non_specificato;\n"
        "- ai_role: generazione_materiali | suggerimento_strategie | adattamento_contenuti | feedback | altro | non_specificato;\n"
        "- practice_present e' booleano."
    ),
    aggregate_mode="individualization",
)


if __name__ == "__main__":
    run(CONFIG)
