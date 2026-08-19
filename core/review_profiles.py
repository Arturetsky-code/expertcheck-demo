
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ReviewProfile:
    code: str
    name: str
    description: str
    include_families: tuple[str,...]
    include_unknown: bool
    run_ocr: bool
    run_ai: bool
    depth_label: str

PROFILES={
 "quick":ReviewProfile(
   "quick","Быстрая","Основные разделы ПД для состава объектов, ключевых ТЭП и межраздельной сверки.",
   ("Пояснительная записка","Генеральный план","Архитектурные решения","Конструктивные решения",
    "Технологические решения","Инженерные системы","Пожарная безопасность","ООС"),
   False,False,True,"Основные разделы ПД"),
 "extended":ReviewProfile(
   "extended","Расширенная — рекомендуется","ПД + инженерные изыскания + ключевая ИРД. Оптимальный режим перед экспертизой.",
   ("Пояснительная записка","Генеральный план","Архитектурные решения","Конструктивные решения",
    "Технологические решения","Инженерные системы","Пожарная безопасность","ООС",
    "Инженерные изыскания","Исходно-разрешительная документация"),
   True,True,True,"ПД + ИИ + ключевая ИРД"),
 "full":ReviewProfile(
   "full","Полная","Весь загруженный комплект, включая приложения, ИРД, сканы и вспомогательные материалы.",
   (),True,True,True,"Полный предэкспертный аудит"),
}

def profile(code:str)->ReviewProfile:
    return PROFILES.get(str(code or "").lower(),PROFILES["extended"])

def filter_prepared_files(files:list[Any], code:str)->tuple[list[Any],list[Any]]:
    p=profile(code)
    if code=="full":
        return list(files),[]
    selected=[];skipped=[]
    for f in files:
        family=str(getattr(f,"document_family","") or "")
        declared=str(getattr(f,"declared_document_type","") or "")
        # Core project documents use declared types; unknowns stay only in extended.
        low=(family+" "+declared).lower()
        if code=="quick":
            tokens=("пз","пзу","ар","кр","тх","иос","пб","оос","генплан","электроснаб","водоснаб")
            ok=any(t in low for t in tokens)
        else:
            ok=True
        (selected if ok else skipped).append(f)
    return selected,skipped
