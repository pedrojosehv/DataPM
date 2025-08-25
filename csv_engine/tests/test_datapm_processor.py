#!/usr/bin/env python3
import os
import io
import csv
import json
import tempfile

from typing import Dict, Any

from csv_engine.engines.datapm_processor import DataPMProcessor
from csv_engine.utils import config


def make_processor_stub() -> DataPMProcessor:
    # Use a stubbed LLM to avoid network calls in tests
    return DataPMProcessor(llm_type="stub")


def test_post_process_title_exact_en():
    p = make_processor_stub()
    llm = p.get_default_response()
    llm["job_title_original"] = "Product Manager"
    llm["job_title_raw"] = "Product Manager"
    llm["skills_detected"] = []
    llm["software_detected"] = []
    out = p._post_process("desc", llm)
    assert out["job_title_normalized"] == "Product Manager"
    assert isinstance(out["confidence_scores"], dict)


def test_post_process_title_fuzzy_en():
    p = make_processor_stub()
    llm = p.get_default_response()
    llm["job_title_original"] = "Data scientst"
    llm["job_title_raw"] = "Data scientst"
    out = p._post_process("desc", llm)
    assert out["job_title_normalized"] == "UNMAPPED"
    sugg = out["_mapping_decisions"]["title"]["suggestions"]
    assert isinstance(sugg, list) and len(sugg) <= 3


def test_post_process_skills_software_en():
    p = make_processor_stub()
    llm = p.get_default_response()
    llm["skills_detected"] = [{"text": "Product Management", "span": [0, 5]}, {"text": "Scrum", "span": [10, 15]}]
    llm["software_detected"] = [{"text": "Power BI", "span": [0, 7]}, {"text": "Tableau", "span": [8, 14]}]
    out = p._post_process("desc", llm)
    skills_norm = out["skills_normalized"]
    sw_norm = out["software_normalized"]
    assert any(item.get("canonical") == "Product Management" for item in skills_norm)
    assert any(item.get("canonical") == "Scrum" for item in skills_norm)
    assert any(item.get("canonical") == "Power BI" for item in sw_norm)
    assert any(item.get("canonical") == "Tableau" for item in sw_norm)


def test_post_process_title_es_unmapped():
    p = make_processor_stub()
    llm = p.get_default_response()
    llm["job_title_original"] = "Analista de Datos"
    llm["job_title_raw"] = "Analista de Datos"
    out = p._post_process("desc", llm)
    assert out["job_title_normalized"] == "UNMAPPED"
    assert len(out["_mapping_decisions"]["title"]["suggestions"]) > 0


def test_post_process_skills_es_with_suggestions():
    p = make_processor_stub()
    llm = p.get_default_response()
    llm["skills_detected"] = [{"text": "Gestión de Producto", "span": [0, 10]}]
    out = p._post_process("desc", llm)
    assert out["skills_normalized"][0]["canonical"] in ("Product Management", "UNMAPPED")
    assert len(out["skills_normalized"][0]["suggestions"]) <= 3


def test_write_final_csv_header_order(tmp_path):
    p = make_processor_stub()
    rows = [
        {"Job title (original)": "X", "Company": "C"},
        {"Job title (short)": "Y", "Skills": "A;B"},
    ]
    out_path = os.path.join(tmp_path, "out.csv")
    p.write_final_csv(rows, out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == [
        "Job title (original)","Job title (short)","Company","Country","State","City","Schedule type","Experience years","Seniority","Skills","Degrees","Software"
    ]


def test_post_process_software_es_exact():
    p = make_processor_stub()
    llm = p.get_default_response()
    llm["software_detected"] = [{"text": "Power BI", "span": [0, 7]}]
    out = p._post_process("descripcion en español", llm)
    assert any(item.get("canonical") == "Power BI" for item in out["software_normalized"])


