from __future__ import annotations

import io
import zipfile

from core.project_upload import (
    PreparedUpload,
    apply_document_type_overrides,
    document_family,
    guess_document_type,
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


def test_reject_zip_traversal():
    archive = make_zip({"../secret.pdf": b"%PDF-test", "ok/АР1.pdf": b"%PDF-test"})
    result = prepare_uploads([Upload("project.zip", archive)])
    assert len(result.files) == 1
    assert any("небезопасный" in warning.lower() for warning in result.warnings)


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
