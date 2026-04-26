#!/usr/bin/env python3
from __future__ import annotations

from ai_usage_qwen_common import (
    LABELS_DIR,
    USAGE_CATEGORIES,
    AnalysisConfig,
    run,
)


CONFIG = AnalysisConfig(
    name="ai-pro-con",
    logger_name="ai_pro_con_qwen_by_cohort",
    schema_version="ai_pro_con.v1",
    default_output_dir=LABELS_DIR / "ollama-qwen3-5-9b-ai-pro-con",
    description="Estrazione qualitativa di pro e contro dell'uso dell'IA nel corpus PRAXIS con Qwen.",
    no_item_status="no_pro_con_item",
    question_needles=(
        "pro e i contro dell uso dell intelligenza artificiale nell educazione",
        "pro e i contro dell uso dell intelligenza artificiale nello studio",
    ),
    allowed_groups=None,
    system_prompt="""Sei un analista qualitativo in ambito educativo.
Analizza esclusivamente il testo della risposta del partecipante.

Devi estrarre pro e contro dichiarati sull'uso dell'intelligenza artificiale.
Non inventare benefici o rischi non presenti. Se il testo e' generico o vuoto, usa liste vuote.
Restituisci solo JSON valido.
""",
    task_prompt=(
        "Estrai, per ogni risposta, i pro e i contro dell'uso dell'IA. "
        "Ogni pro/contro deve avere una categoria, una breve evidenza testuale e una ragione sintetica."
    ),
    output_example="""{
  "items": [
    {
      "index": 7,
      "stance": "misto",
      "pros": [
        {
          "category": "efficienza_tempo",
          "evidence": "risparmio di tempo",
          "reason": "Il partecipante indica un vantaggio operativo."
        }
      ],
      "cons": [
        {
          "category": "delega_cognitiva",
          "evidence": "non ti fa ragionare",
          "reason": "Il partecipante segnala perdita di ragionamento autonomo."
        }
      ],
      "confidence": 0.8,
      "reason": "La risposta contiene sia un beneficio sia un rischio."
    }
  ]
}""",
    allowed_values_text=(
        "- stance: solo_pro | solo_contro | misto | nessuno;\n"
        f"- category per pros/cons: {' | '.join(USAGE_CATEGORIES)};\n"
        "- pros e cons sono liste, anche vuote."
    ),
    aggregate_mode="pro_con",
)


if __name__ == "__main__":
    run(CONFIG)
