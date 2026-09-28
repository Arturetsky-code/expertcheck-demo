from __future__ import annotations

import io
import re
import shutil
import tempfile
import zipfile
import hashlib
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree as ET

SUPPORTED_EXTENSIONS = {".pdf", ".xml"}
IGNORED_NAMES = {"thumbs.db", ".ds_store"}
MAX_ARCHIVE_ENTRIES = 2500
MAX_UNCOMPRESSED_BYTES = 1_500 * 1024 * 1024

DOCUMENT_TYPE_OPTIONS = [
    "Не определён", "ПЗ", "ПЗ XML", "ПЗУ1", "ПЗУ2", "АР1", "АР2", "АР", "КР",
    "ТХ1", "ТХ2", "ТХ", "ИОС1", "ИОС2", "ИОС3", "ИОС4", "ИОС5", "ИОС6", "ИОС7",
    "ПОС", "ПОД", "ПБ", "ООС", "ОДИ", "ЭЭ", "СМ", "ППО", "ТКР", "ИЛО", "ГОЧС",
    "ИГДИ", "ИГИ", "ИГМИ", "ИЭИ", "ТУ", "ИРД", "Исходные данные",
    "Задание на проектирование", "Прочее",
]


@dataclass
class PreparedUpload:
    name: str
    data: bytes | None
    declared_document_type: str = ""
    source_container: str = ""
    relative_path: str = ""
    backing_path: str = ""
    backing_size: int = 0

    @property
    def size(self) -> int:
        if self.data is not None:
            return len(self.data)
        if self.backing_size:
            return int(self.backing_size)
        if self.backing_path:
            try:
                return int(Path(self.backing_path).stat().st_size)
            except OSError:
                return 0
        return 0

    @property
    def file_backed(self) -> bool:
        return bool(self.backing_path and self.data is None)

    def getvalue(self) -> bytes:
        if self.data is not None:
            return self.data
        if not self.backing_path:
            return b""
        return Path(self.backing_path).read_bytes()

    def read(self, *args: Any, **kwargs: Any) -> bytes:
        return self.getvalue()

    def with_document_type(self, document_type: str) -> "PreparedUpload":
        return replace(self, declared_document_type=document_type or "")


@dataclass
class UploadPreparationResult:
    files: list[PreparedUpload]
    inventory: list[dict[str, Any]]
    warnings: list[str]
    errors: list[str]
    package_summary: dict[str, Any]
    temp_resources: list[Any] = field(default_factory=list, repr=False)


def _clean_path(name: str) -> str:
    return str(PurePosixPath(str(name).replace("\\", "/")))


def _safe_zip_member(name: str) -> bool:
    path = PurePosixPath(_clean_path(name))
    return not path.is_absolute() and ".." not in path.parts


def _extension(name: str) -> str:
    return PurePosixPath(name).suffix.lower()


def guess_document_type(filename: str) -> str:
    """Определяет раздел только по имени файла для предварительного экрана.

    Это не заменяет содержательную классификацию анализатора. Пользователь может
    исправить результат до запуска анализа.
    """
    name = re.sub(r"[\s_\-–—]+", " ", filename.lower())
    ext = _extension(filename)
    if ext == ".xml":
        return "ПЗ XML"
    patterns: list[tuple[str, tuple[str, ...]]] = [
        ("ПЗУ2", ("пзу2", "пзу 2", "графическая часть пзу", "генеральный план")),
        ("ПЗУ1", ("пзу1", "пзу 1", "текстовая часть пзу")),
        ("АР2", ("ар2", "ар 2", "графическая часть ар")),
        ("АР1", ("ар1", "ар 1", "текстовая часть ар")),
        ("ТХ2", ("тх2", "тх 2", "графическая часть тх")),
        ("ТХ1", ("тх1", "тх 1", "текстовая часть тх")),
        # Explicit source-document roles must win over thematic PD words.
        # Example: "ТУ_электроснабжение.pdf" is a technical-condition source,
        # not an ИОС1 project section.
        ("ТУ", ("технические условия", "техусловия", " ту ")),
        ("Исходные данные", ("исходные данные", "исходные материалы")),
        ("ИРД", ("исходно разрешительная", "исходно-разрешительная", " ирд ")),
        ("ИОС1", ("иос1", "иос 1", "электроснаб", " эс ")),
        ("ИОС2", ("иос2", "иос 2", "водоснаб")),
        ("ИОС3", ("иос3", "иос 3", "водоотвед", "канализац")),
        ("ИОС4", ("иос4", "иос 4", "отоплен", "вентиляц")),
        ("ИОС5", ("иос5", "иос 5", "связ")),
        ("ИОС6", ("иос6", "иос 6", "газоснаб")),
        ("ИОС7", ("иос7", "иос 7", "технологические решения")),
        ("ПЗ", ("раздел пд №1", "раздел 1", " пояснительная записка", " пз")),
        ("КР", (" кр", "конструктив")),
        ("АР", (" ар", "архитектур")),
        ("ТХ", (" тх", "технологич")),
        ("ПОС", (" пос", "организац строительства")),
        ("ПБ", (" пб", "пожарн")),
        ("ООС", (" оос", "окружающей среды")),
        ("ОДИ", (" оди", "доступности инвалид")),
        ("ГОЧС", ("гочс", "чрезвычай")),
        ("ИГДИ", ("игди", "геодез")),
        ("ИГИ", ("иги", "геолог")),
        ("ИГМИ", ("игми", "гидрометеорол")),
        ("ИЭИ", ("иэи", "экологическ")),
        ("Задание на проектирование", ("задание на проектирование", "техническое задание", "тз на проектирование", "знп")),
    ]
    padded = f" {name} "
    for doc_type, aliases in patterns:
        if any(alias in padded for alias in aliases):
            return doc_type
    return "Не определён"


def document_family(document_type: str) -> str:
    value = str(document_type or "").upper().replace(" ", "")
    if value.startswith("ПЗУ"):
        return "ПЗУ"
    if value.startswith("АР"):
        return "АР"
    if value.startswith("ТХ"):
        return "ТХ"
    if value.startswith("ИОС1"):
        return "ИОС1"
    if value.startswith("ИОС2"):
        return "ИОС2"
    if value.startswith("ИОС3"):
        return "ИОС3"
    if value.startswith("ИОС4"):
        return "ИОС4"
    if value == "ПЗXML":
        return "ПЗ XML"
    if value in {"ИГДИ", "ИГИ", "ИГМИ", "ИЭИ"}:
        return "Инженерные изыскания"
    if value == "ТУ":
        return "ТУ"
    if value in {"ИРД", "ИСХОДНЫЕДАННЫЕ"}:
        return "ИРД"
    return document_type or "Не определён"


def _extract_zip(
    uploaded: Any,
    errors: list[str],
    warnings: list[str],
    temp_dir: Path,
) -> list[PreparedUpload]:
    """Extract supported ZIP members to temporary files instead of RAM.

    Streamlit already holds the uploaded ZIP. Keeping every uncompressed PDF/XML
    as a second in-memory copy makes large packages peak at roughly ZIP + full
    uncompressed content. File-backed members keep the prepared package bounded:
    each downstream analyzer materializes only the file it is currently reading.
    """
    output: list[PreparedUpload] = []
    archive_name = str(getattr(uploaded, "name", "project.zip"))
    try:
        if hasattr(uploaded, "read") and hasattr(uploaded, "seek"):
            try:
                uploaded.seek(0)
                source = uploaded
            except Exception:
                source = io.BytesIO(uploaded.getvalue())
        else:
            source = io.BytesIO(uploaded.getvalue())
        with zipfile.ZipFile(source) as archive:
            infos = [i for i in archive.infolist() if not i.is_dir()]
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                errors.append(f"Архив {archive_name}: слишком много файлов ({len(infos)}).")
                return []
            total = sum(max(0, info.file_size) for info in infos)
            if total > MAX_UNCOMPRESSED_BYTES:
                errors.append(
                    f"Архив {archive_name}: распакованный объём превышает "
                    f"{MAX_UNCOMPRESSED_BYTES / 1024 / 1024:.0f} МБ."
                )
                return []
            for info in infos:
                member = _clean_path(info.filename)
                if not _safe_zip_member(member):
                    warnings.append(f"Пропущен небезопасный путь в архиве: {info.filename}")
                    continue
                base = PurePosixPath(member).name
                ext = _extension(member)
                if base.lower() in IGNORED_NAMES or base.startswith(".") or "/__macosx/" in f"/{member.lower()}/":
                    continue
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                digest = hashlib.blake2b(member.encode("utf-8", "ignore"), digest_size=8).hexdigest()
                target = temp_dir / f"{len(output):05d}_{digest}{ext}"
                try:
                    with archive.open(info, "r") as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                except Exception as exc:
                    warnings.append(f"Не удалось извлечь {member} из {archive_name}: {exc}")
                    try:
                        target.unlink(missing_ok=True)
                    except Exception:
                        pass
                    continue
                display_name = member
                output.append(
                    PreparedUpload(
                        name=display_name,
                        data=None,
                        declared_document_type=guess_document_type(display_name),
                        source_container=archive_name,
                        relative_path=member,
                        backing_path=str(target),
                        backing_size=int(info.file_size or 0),
                    )
                )
    except zipfile.BadZipFile:
        errors.append(f"Файл {archive_name} не является корректным ZIP-архивом.")
    except Exception as exc:
        errors.append(f"Не удалось открыть архив {archive_name}: {exc}")
    return output


def _direct_upload(uploaded: Any) -> PreparedUpload | None:
    name = str(getattr(uploaded, "name", "document"))
    ext = _extension(name)
    if ext not in SUPPORTED_EXTENSIONS:
        return None
    return PreparedUpload(
        name=name,
        data=uploaded.getvalue(),
        declared_document_type=guess_document_type(name),
        source_container="Прямая загрузка",
        relative_path=name,
    )


def _quick_identity(file: PreparedUpload) -> dict[str, str]:
    result = {"project_code": "", "project_name": "", "year": "", "xml_schema": ""}
    try:
        if _extension(file.name) == ".xml":
            root = ET.fromstring(file.getvalue())
            result["xml_schema"] = str(root.attrib.get("SchemaVersion", ""))
            for tag in ("ExplanatoryNoteNumber", "ProjectDocumentationNumber"):
                node = root.find(f".//{tag}")
                if node is not None and node.text:
                    result["project_code"] = node.text.strip()
                    break
            node = root.find(".//ExplanatoryNoteYear")
            if node is not None and node.text:
                result["year"] = node.text.strip()
            for xpath in (".//NonIndustrialObject/Name", ".//IndustrialObject/Name", ".//LinearObject/Name", ".//Name"):
                node = root.find(xpath)
                if node is not None and node.text and len(node.text.strip()) > 12:
                    result["project_name"] = node.text.strip()
                    break
        elif _extension(file.name) == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=file.getvalue(), filetype="pdf")
                text = "\n".join(page.get_text("text") for page in list(doc)[:2])
                doc.close()
                code_match = re.search(r"\b[A-ZА-Я0-9]{2,}(?:[-.–—][A-ZА-Я0-9.№]+){2,}\b", text)
                if code_match:
                    result["project_code"] = code_match.group(0).strip(".,;:")
                year_match = re.search(r"\b20\d{2}\b", text)
                if year_match:
                    result["year"] = year_match.group(0)
            except Exception:
                pass
    except Exception:
        pass
    return result


def _package_checks(files: list[PreparedUpload]) -> tuple[list[str], dict[str, Any]]:
    warnings: list[str] = []
    identities = [_quick_identity(file) for file in files]
    codes = sorted({x["project_code"] for x in identities if x["project_code"]})
    years = sorted({x["year"] for x in identities if x["year"]})
    schemas = sorted({x["xml_schema"] for x in identities if x["xml_schema"]})
    if len(codes) > 1:
        warnings.append("Обнаружено несколько шифров проекта: " + "; ".join(codes[:8]))
    if len(years) > 1:
        warnings.append("В комплекте обнаружены документы разных годов: " + ", ".join(years))
    names = [file.name.lower() for file in files]
    duplicate_basenames = sorted({PurePosixPath(name).name for name in names if sum(PurePosixPath(x).name == PurePosixPath(name).name for x in names) > 1})
    if duplicate_basenames:
        warnings.append("Есть файлы с одинаковыми именами в разных папках: " + ", ".join(duplicate_basenames[:8]))
    return warnings, {"project_codes": codes, "years": years, "xml_schemas": schemas}


def _completeness(files: list[PreparedUpload]) -> dict[str, Any]:
    families = {document_family(file.declared_document_type) for file in files}
    required = ["ПЗ", "ПЗ XML", "ПЗУ", "АР", "ТХ"]
    present = {name: name in families for name in required}
    available_checks: list[str] = []
    limitations: list[str] = []
    if present["ПЗ"] and present["ПЗ XML"]:
        available_checks.append("PDF ПЗ ↔ XML ПЗ")
    else:
        limitations.append("Сверка PDF ПЗ ↔ XML ограничена")
    if present["ПЗ"] and present["ПЗУ"]:
        available_checks.append("ПЗ ↔ ПЗУ и реестр генплана")
    else:
        limitations.append("Контроль перечня объектов по генплану ограничен")
    if present["ПЗ"] and present["АР"]:
        available_checks.append("ПЗ ↔ АР: площади, объёмы, высота, этажность")
    else:
        limitations.append("Архитектурные ТЭП не будут полноценно подтверждены")
    if present["ПЗ"] and present["ТХ"]:
        available_checks.append("ПЗ ↔ ТХ: производительность, персонал, оборудование")
    else:
        limitations.append("Технологические показатели не будут полноценно подтверждены")
    return {"present": present, "available_checks": available_checks, "limitations": limitations}


def _traceability_source_summary(files: list[PreparedUpload]) -> dict[str, Any]:
    counts = {
        "SURVEY_REPORT": 0,
        "TECHNICAL_CONDITIONS": 0,
        "SOURCE_DATA": 0,
    }
    for file in files:
        dtype = str(file.declared_document_type or "").upper().replace(" ", "")
        if dtype in {"ИГДИ", "ИГИ", "ИГМИ", "ИЭИ"}:
            counts["SURVEY_REPORT"] += 1
        elif dtype == "ТУ":
            counts["TECHNICAL_CONDITIONS"] += 1
        elif dtype in {"ИРД", "ИСХОДНЫЕДАННЫЕ"}:
            counts["SOURCE_DATA"] += 1

    available = [role for role, count in counts.items() if count > 0]
    missing = [role for role, count in counts.items() if count == 0]
    return {
        "source_role_counts": counts,
        "available_source_roles": available,
        "missing_source_roles": missing,
        "traceability_ready": bool(available),
    }


def _content_digest(file: PreparedUpload) -> str:
    digest = hashlib.blake2b(digest_size=12)
    if file.data is not None:
        digest.update(file.data)
        return digest.hexdigest()
    if file.backing_path:
        try:
            with Path(file.backing_path).open("rb") as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
            return digest.hexdigest()
        except OSError:
            return ""
    return ""


def prepare_uploads(uploaded_files: Iterable[Any]) -> UploadPreparationResult:
    files: list[PreparedUpload] = []
    warnings: list[str] = []
    errors: list[str] = []
    temp_resources: list[Any] = []
    zip_temp: tempfile.TemporaryDirectory[str] | None = None
    for uploaded in uploaded_files or []:
        name = str(getattr(uploaded, "name", ""))
        try:
            if _extension(name) == ".zip":
                if zip_temp is None:
                    zip_temp = tempfile.TemporaryDirectory(prefix="expertcheck_upload_")
                    temp_resources.append(zip_temp)
                files.extend(_extract_zip(uploaded, errors, warnings, Path(zip_temp.name)))
            else:
                prepared = _direct_upload(uploaded)
                if prepared:
                    files.append(prepared)
                else:
                    warnings.append(f"Файл {name} пропущен: поддерживаются PDF, XML и ZIP.")
        except Exception as exc:
            # Не останавливаем загрузку всего комплекта из-за одного проблемного файла.
            warnings.append(f"Не удалось подготовить файл {name}: {type(exc).__name__}: {exc}")

    # Удаляем точные дубли по пути и содержимому, но не объединяем одноимённые разные файлы.
    unique: list[PreparedUpload] = []
    seen: set[tuple[str, int, int]] = set()
    for file in files:
        signature = (file.name.lower(), file.size, _content_digest(file))
        if signature in seen:
            warnings.append(f"Удалён полный дубль: {file.name}")
            continue
        seen.add(signature)
        unique.append(file)
    files = unique

    package_warnings, identity_summary = _package_checks(files)
    warnings.extend(package_warnings)
    completeness = _completeness(files)
    inventory: list[dict[str, Any]] = []
    for idx, file in enumerate(files):
        inventory.append({
            "ID": idx,
            "Файл": file.name,
            "Формат": _extension(file.name).lstrip(".").upper(),
            "Предполагаемый раздел": file.declared_document_type or "Не определён",
            "Семейство": document_family(file.declared_document_type),
            "Размер, МБ": round(file.size / 1024 / 1024, 2),
            "Источник": file.source_container,
            "Статус": "Готов" if file.declared_document_type != "Не определён" else "Уточнить раздел",
        })
    summary = {
        "files": len(files),
        "total_bytes": sum(file.size for file in files),
        "identity": identity_summary,
        "completeness": completeness,
        "traceability": _traceability_source_summary(files),
        "storage": {
            "file_backed_files": sum(1 for file in files if file.file_backed),
            "in_memory_files": sum(1 for file in files if not file.file_backed),
            "file_backed_bytes": sum(file.size for file in files if file.file_backed),
        },
    }
    return UploadPreparationResult(files, inventory, warnings, errors, summary, temp_resources)


def merge_prepared_packages(
    base: UploadPreparationResult,
    addition: UploadPreparationResult,
) -> UploadPreparationResult:
    """Merge sequentially staged upload parts without rematerialising file bytes.

    Temporary-directory owners from every part are retained by the merged result,
    so file-backed members stay readable after the intermediate package objects
    leave scope.
    """
    files: list[PreparedUpload] = []
    warnings = list(base.warnings or []) + list(addition.warnings or [])
    errors = list(base.errors or []) + list(addition.errors or [])
    temp_resources = list(base.temp_resources or []) + list(addition.temp_resources or [])

    seen: set[tuple[str, int, str]] = set()
    for file in list(base.files or []) + list(addition.files or []):
        signature = (file.name.lower(), file.size, _content_digest(file))
        if signature in seen:
            warnings.append(f"Удалён полный дубль между частями комплекта: {file.name}")
            continue
        seen.add(signature)
        files.append(file)

    package_warnings, identity_summary = _package_checks(files)
    warnings.extend(package_warnings)
    warnings = list(dict.fromkeys(str(item) for item in warnings if str(item).strip()))
    errors = list(dict.fromkeys(str(item) for item in errors if str(item).strip()))

    inventory: list[dict[str, Any]] = []
    for idx, file in enumerate(files):
        inventory.append({
            "ID": idx,
            "Файл": file.name,
            "Формат": _extension(file.name).lstrip(".").upper(),
            "Предполагаемый раздел": file.declared_document_type or "Не определён",
            "Семейство": document_family(file.declared_document_type),
            "Размер, МБ": round(file.size / 1024 / 1024, 2),
            "Источник": file.source_container,
            "Статус": "Готов" if file.declared_document_type != "Не определён" else "Уточнить раздел",
        })

    summary = {
        "files": len(files),
        "total_bytes": sum(file.size for file in files),
        "identity": identity_summary,
        "completeness": _completeness(files),
        "traceability": _traceability_source_summary(files),
        "storage": {
            "file_backed_files": sum(1 for file in files if file.file_backed),
            "in_memory_files": sum(1 for file in files if not file.file_backed),
            "file_backed_bytes": sum(file.size for file in files if file.file_backed),
        },
        "staged_parts": int((base.package_summary or {}).get("staged_parts") or 1)
            + int((addition.package_summary or {}).get("staged_parts") or 1),
    }
    return UploadPreparationResult(
        files, inventory, warnings, errors, summary, temp_resources
    )


def apply_document_type_overrides(
    files: list[PreparedUpload],
    inventory_rows: Iterable[dict[str, Any]],
) -> list[PreparedUpload]:
    overrides: dict[int, str] = {}
    for row in inventory_rows:
        try:
            idx = int(row.get("ID"))
        except (TypeError, ValueError):
            continue
        overrides[idx] = str(row.get("Предполагаемый раздел") or "")
    result: list[PreparedUpload] = []
    for idx, file in enumerate(files):
        result.append(file.with_document_type(overrides.get(idx, file.declared_document_type)))
    return result
