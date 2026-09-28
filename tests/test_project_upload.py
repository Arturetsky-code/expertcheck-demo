from __future__ import annotations

import io
import zipfile
from pathlib import Path

from core.project_upload import (
    PreparedUpload,
    apply_document_type_overrides,
    document_family,
    guess_document_type,
    merge_prepared_packages,
    prepare_uploads,
)


class Upload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def make_zip(entries: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return stream.getvalue()


def test_guess_document_type():
    assert guess_document_type("Раздел ПД № 2_ПЗУ2.pdf") == "ПЗУ2"
    assert guess_document_type("Раздел ПД № 3_АР1.pdf") == "АР1"
    assert guess_document_type("Раздел ПД №1_ПЗ.xml") == "ПЗ XML"
    assert document_family("АР2") == "АР"


def test_guess_traceability_source_document_types():
    assert guess_document_type("ИГИ_Технический_отчет.pdf") == "ИГИ"
    assert guess_document_type("ТУ_электроснабжение_№15.pdf") == "ТУ"
    assert guess_document_type("Исходные данные заказчика.pdf") == "Исходные данные"
    assert guess_document_type("ИРД_перечень.pdf") == "ИРД"
    assert document_family("ИГМИ") == "Инженерные изыскания"
    assert document_family("Исходные данные") == "ИРД"


def test_traceability_source_summary_counts_real_source_roles():
    files = [
        Upload("ИГИ_Технический_отчет.pdf", b"%PDF"),
        Upload("ТУ_электроснабжение.pdf", b"%PDF"),
        Upload("Исходные данные заказчика.pdf", b"%PDF"),
        Upload("Раздел ПД №1_ПЗ.pdf", b"%PDF"),
    ]
    result = prepare_uploads(files)
    trace = result.package_summary["traceability"]
    assert trace["source_role_counts"] == {
        "SURVEY_REPORT": 1,
        "TECHNICAL_CONDITIONS": 1,
        "SOURCE_DATA": 1,
    }
    assert trace["traceability_ready"] is True
    assert trace["missing_source_roles"] == []


def test_traceability_source_summary_reports_missing_sources_without_blocking_upload():
    result = prepare_uploads([Upload("Раздел ПД №1_ПЗ.pdf", b"%PDF")])
    trace = result.package_summary["traceability"]
    assert trace["traceability_ready"] is False
    assert set(trace["missing_source_roles"]) == {
        "SURVEY_REPORT", "TECHNICAL_CONDITIONS", "SOURCE_DATA"
    }


def test_prepare_zip_and_ignore_service_files():
    archive = make_zip({
        "project/Раздел ПД №1_ПЗ.pdf": b"%PDF-test",
        "project/Раздел ПД №1_ПЗ.xml": b"<?xml version='1.0'?><ExplanatoryNote SchemaVersion='01.07'/>",
        "project/readme.txt": b"ignored",
        "__MACOSX/._file.pdf": b"ignored",
    })
    result = prepare_uploads([Upload("project.zip", archive)])
    assert not result.errors
    assert len(result.files) == 2
    assert {x.declared_document_type for x in result.files} == {"ПЗ", "ПЗ XML"}


def test_zip_members_are_file_backed_and_readable():
    payload = b"%PDF-file-backed-test"
    archive = make_zip({"project/Раздел ПД №1_ПЗ.pdf": payload})
    result = prepare_uploads([Upload("project.zip", archive)])
    assert not result.errors
    assert len(result.files) == 1
    prepared = result.files[0]
    assert prepared.data is None
    assert prepared.file_backed is True
    assert prepared.backing_path
    assert prepared.getvalue() == payload
    assert result.package_summary["storage"]["file_backed_files"] == 1
    assert result.package_summary["storage"]["in_memory_files"] == 0
    assert result.package_summary["storage"]["file_backed_bytes"] == len(payload)


def test_direct_upload_remains_in_memory():
    payload = b"%PDF-direct-test"
    result = prepare_uploads([Upload("Раздел ПД №1_ПЗ.pdf", payload)])
    assert len(result.files) == 1
    prepared = result.files[0]
    assert prepared.data == payload
    assert prepared.file_backed is False
    assert prepared.getvalue() == payload
    assert result.package_summary["storage"]["in_memory_files"] == 1


def test_reject_zip_traversal():
    archive = make_zip({"../secret.pdf": b"%PDF-test", "ok/АР1.pdf": b"%PDF-test"})
    result = prepare_uploads([Upload("project.zip", archive)])
    assert len(result.files) == 1
    assert any("небезопасный" in warning.lower() for warning in result.warnings)


def test_merge_prepared_zip_parts_keeps_file_backing_alive():
    left = prepare_uploads([Upload(
        "part-1.zip",
        make_zip({"a/ИГИ_Технический_отчет.pdf": b"%PDF-survey"})
    )])
    right = prepare_uploads([Upload(
        "part-2.zip",
        make_zip({"b/Раздел ПД №1_ПЗ.pdf": b"%PDF-project"})
    )])

    merged = merge_prepared_packages(left, right)
    assert len(merged.files) == 2
    assert all(item.file_backed for item in merged.files)
    assert merged.package_summary["staged_parts"] == 2
    assert merged.package_summary["storage"]["file_backed_files"] == 2
    assert merged.package_summary["traceability"]["source_role_counts"]["SURVEY_REPORT"] == 1

    paths = [item.backing_path for item in merged.files]
    del left, right
    import gc
    gc.collect()
    assert all(Path(path).exists() for path in paths)
    assert {item.getvalue() for item in merged.files} == {b"%PDF-survey", b"%PDF-project"}


def test_merge_prepared_zip_parts_deduplicates_exact_member():
    payload = b"%PDF-same"
    left = prepare_uploads([Upload("part-1.zip", make_zip({"same.pdf": payload}))])
    right = prepare_uploads([Upload("part-2.zip", make_zip({"same.pdf": payload}))])

    merged = merge_prepared_packages(left, right)
    assert len(merged.files) == 1
    assert any("дубль между частями" in warning.lower() for warning in merged.warnings)
    assert merged.package_summary["staged_parts"] == 2


def test_apply_overrides():
    files = [PreparedUpload("unknown.pdf", b"x", "Не определён")]
    updated = apply_document_type_overrides(files, [{"ID": 0, "Предполагаемый раздел": "ТХ1"}])
    assert updated[0].declared_document_type == "ТХ1"


def test_completeness_summary():
    files = [
        Upload("Раздел ПД №1_ПЗ.pdf", b"%PDF"),
        Upload("Раздел ПД №1_ПЗ.xml", b"<?xml version='1.0'?><ExplanatoryNote SchemaVersion='01.07'/>")
    ]
    result = prepare_uploads(files)
    present = result.package_summary["completeness"]["present"]
    assert present["ПЗ"] is True
    assert present["ПЗ XML"] is True
    assert present["АР"] is False
