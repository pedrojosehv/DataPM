#!/usr/bin/env python3
"""
DataPM Processor - Extracción con NER (Hugging Face)
Extrae entidades clave de descripciones de empleo usando un modelo NER open source
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import pandas as pd
from transformers import pipeline

class DataPMProcessorNER:
    """Procesador para extracción de entidades con NER"""
    def __init__(self, model: str = "dslim/bert-base-NER"):
        self.model = model
        self.ner = pipeline("ner", model=self.model, aggregation_strategy="simple")

    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = self.ner(text)
        # Mapeo simple: puedes mejorar esto según tus necesidades
        result = {"ORG": [], "LOC": [], "PER": [], "MISC": []}
        for ent in entities:
            label = ent["entity_group"]
            if label in result:
                result[label].append(ent["word"])
        return result

    def process_description(self, row: Dict[str, Any]) -> Dict[str, Any]:
        description = row.get('description', '')
        ents = self.extract_entities(description)
        # Inferir campos usando NER y reglas simples
        return {
            'Job title (original)': row.get('title', 'Unknown'),
            'Job title (short)': row.get('title', 'Unknown'),  # Mejorar con reglas si es posible
            'Company': ', '.join(ents['ORG']) if ents['ORG'] else row.get('company', 'Unknown'),
            'Country': ', '.join(ents['LOC']) if ents['LOC'] else 'Unknown',
            'State': 'Unknown',
            'City': 'Unknown',
            'Schedule type': 'Unknown',
            'Experience years': 'Unknown',
            'Seniority': 'Unknown',
            'Skills': '',
            'Degrees': '',
            'Software': ''
        }

    def process_csv(self, input_file: str, output_file: Optional[str] = None, nrows: int = 5):
        print(f"📖 Leyendo las primeras {nrows} filas de: {input_file}")
        df = pd.read_csv(input_file, nrows=nrows)
        results = []
        for i, row in df.iterrows():
            res = self.process_description(row)
            results.append(res)
        out_path = output_file or f"csv/archive/{datetime.now().strftime('%Y%m%d_%H%M%S')}_DataPM_NER_result.csv"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        pd.DataFrame(results).to_csv(out_path, index=False)
        print(f"✅ Guardado: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="DataPM Processor (NER) - Extracción de entidades de descripciones de trabajo")
    parser.add_argument("input_file", help="Archivo CSV de entrada")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida (opcional)")
    parser.add_argument("--model", default="dslim/bert-base-NER", help="Modelo NER de Hugging Face (default: dslim/bert-base-NER)")
    parser.add_argument("--nrows", type=int, default=5, help="Número de filas a procesar (default: 5)")
    args = parser.parse_args()
    processor = DataPMProcessorNER(model=args.model)
    processor.process_csv(args.input_file, args.output, nrows=args.nrows)

if __name__ == "__main__":
    main()
