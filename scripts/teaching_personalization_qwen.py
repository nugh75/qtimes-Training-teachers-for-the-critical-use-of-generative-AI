#!/usr/bin/env python3
from __future__ import annotations

from ai_usage_qwen_common import (
    LABELS_DIR,
    PERSONALIZATION_STRATEGIES,
    TEACHER_GROUPS,
    AnalysisConfig,
    run,
)


CONFIG = AnalysisConfig(
    name="teaching-personalization",
    logger_name="teaching_personalization_qwen",
    schema_version="teaching_personalization.v1",
    default_output_dir=LABELS_DIR / "ollama-qwen3-5-9b-teaching-personalization",
    description="Analisi qualitativa della personalizzazione dell'insegnamento con IA, solo insegnanti.",
    no_item_status="no_personalization_item",
    question_needles=(
        "utilizzi l intelligenza artificiale per personalizzare l insegnamento",
    ),
    allowed_groups=TEACHER_GROUPS,
    system_prompt="""Sei un analista qualitativo di pratiche didattiche.
Analizza esclusivamente la risposta del partecipante.

La personalizzazione riguarda possibilita' elettive, interessi, potenzialita', talenti,
modalita' espressive o percorsi personali dello studente. Non confonderla con la sola
individualizzazione per raggiungere obiettivi minimi comuni.
Restituisci solo JSON valido.
""",
    task_prompt=(
        "Classifica come l'insegnante dichiara di usare l'IA per personalizzare "
        "l'insegnamento. Se non descrive una pratica, segnala practice_present=false."
    ),
    output_example="""{
  "items": [
    {
      "index": 4,
      "practice_present": true,
      "strategies": ["materiali_differenziati", "interessi_studenti"],
      "target": "singolo_studente",
      "ai_role": "adattamento_contenuti",
      "evidence": "nelle presentazioni di argomenti",
      "confidence": 0.75,
      "reason": "La risposta indica adattamento di contenuti per esigenze personali."
    }
  ]
}""",
    allowed_values_text=(
        f"- strategies: {' | '.join(PERSONALIZATION_STRATEGIES)};\n"
        "- target: singolo_studente | gruppo_classe | sottogruppo | non_specificato;\n"
        "- ai_role: generazione_materiali | suggerimento_strategie | adattamento_contenuti | feedback | altro | non_specificato;\n"
        "- practice_present e' booleano."
    ),
    aggregate_mode="personalization",
)


if __name__ == "__main__":
    run(CONFIG)
