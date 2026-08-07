from __future__ import annotations
from typing import Any, Iterable


def recover_text_from_scanned_pages(files: Iterable[Any], document_types: dict[str,str], *, max_pages_per_file: int = 4) -> tuple[list[dict[str,Any]], list[dict[str,Any]]]:
    """Best-effort OCR for text-sparse pages.

    Uses PyMuPDF OCR only when the runtime has Tesseract support. It is capped and
    failure-safe for Streamlit Cloud. Returned page text is fed into the same
    strict structure/object engines as ordinary PDF text.
    """
    pages=[]; audit=[]
    try:
        import fitz
    except Exception as exc:
        return [], [{'decision':'unavailable','reason':str(exc)}]
    for file_obj in files:
        name=str(getattr(file_obj,'name',''))
        attempted=0
        try:
            if hasattr(file_obj,'seek'): file_obj.seek(0)
            data=file_obj.read() if hasattr(file_obj,'read') else bytes(file_obj)
            if hasattr(file_obj,'seek'): file_obj.seek(0)
            doc=fitz.open(stream=data,filetype='pdf')
            for idx,page in enumerate(doc):
                native=(page.get_text('text') or '').strip()
                if len(native) >= 25:
                    continue
                images=page.get_images(full=True)
                if not images:
                    continue
                audit.append({'document':name,'page':idx+1,'decision':'scan_detected','native_chars':len(native),'images':len(images)})
                if attempted >= max_pages_per_file:
                    continue
                attempted += 1
                try:
                    tp=page.get_textpage_ocr(dpi=150, full=True)
                    text=(page.get_text('text', textpage=tp) or '').strip()
                except Exception as exc:
                    audit.append({'document':name,'page':idx+1,'decision':'ocr_unavailable','reason':str(exc)[:300]})
                    continue
                if len(text) >= 20:
                    pages.append({'document':name,'document_type':str(document_types.get(name) or ''),'page':idx+1,'text':text,'ocr':True})
                    audit.append({'document':name,'page':idx+1,'decision':'ocr_ok','chars':len(text)})
        except Exception as exc:
            audit.append({'document':name,'decision':'error','reason':str(exc)[:300]})
    return pages,audit
