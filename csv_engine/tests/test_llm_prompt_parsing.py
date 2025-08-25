#!/usr/bin/env python3
import json
from csv_engine.engines.datapm_processor import DataPMProcessor


def test_tolerant_parser_valid():
    p = DataPMProcessor(llm_type="stub")
    mock = '{"job_title_original":"X","job_title_raw":"X","job_title_candidates":[],"job_title_normalized":"UNMAPPED","skills_detected":[],"skills_normalized":[],"software_detected":[],"software_normalized":[],"experience_years":"0-3","experience_years_hint":null,"job_schedule_type":"Full-time","seniority":"Junior","seniority_hint":null,"city":"A","state":"Unknown","country":"Spain","degrees":[],"company_name":"C","confidence_scores":{"title":0.2,"skills":0.1,"software":0.1},"provenance":{}}'
    parsed, cleaned = p._parse_json_tolerant(mock)
    assert isinstance(parsed, dict)
    assert parsed["job_title_original"] == "X"
    assert parsed["job_title_normalized"] == "UNMAPPED"


def test_tolerant_parser_with_backticks_and_json_fence():
    p = DataPMProcessor(llm_type="stub")
    mock = "```json\n{\n  \"job_title_original\": \"X\",\n  \"job_title_raw\": \"X\",\n  \"job_title_candidates\": [],\n  \"job_title_normalized\": \"UNMAPPED\",\n  \"skills_detected\": [],\n  \"skills_normalized\": [],\n  \"software_detected\": [],\n  \"software_normalized\": [],\n  \"experience_years\": \"0-3\",\n  \"experience_years_hint\": null,\n  \"job_schedule_type\": \"Full-time\",\n  \"seniority\": \"Junior\",\n  \"seniority_hint\": null,\n  \"city\": \"A\",\n  \"state\": \"Unknown\",\n  \"country\": \"Spain\",\n  \"degrees\": [],\n  \"company_name\": \"C\",\n  \"confidence_scores\": {\"title\": 0.2, \"skills\": 0.1, \"software\": 0.1},\n  \"provenance\": {}\n}\n```"
    parsed, cleaned = p._parse_json_tolerant(mock)
    assert isinstance(parsed, dict)
    assert parsed["experience_years"] == "0-3"


def test_unmapped_case_suggestions_present():
    p = DataPMProcessor(llm_type="stub")
    llm = p.get_default_response()
    llm["job_title_original"] = "Analista de Datos"
    llm["job_title_raw"] = "Analista de Datos"
    out = p._post_process("desc", llm)
    assert out["job_title_normalized"] == "UNMAPPED"
    assert len(out["_mapping_decisions"]["title"]["suggestions"]) > 0

