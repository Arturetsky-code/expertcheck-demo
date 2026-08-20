from core.checklist_verification import qualify_checklist_results

def test_candidate_checklist_evidence_is_not_completed():
    rows=qualify_checklist_results([{'question':'Проверить решение','status':'Требует проверки','proof_kind':'CANDIDATE_EVIDENCE','evidence':'Есть тематический фрагмент'}])
    assert rows[0]['verification_kind']=='REVIEW_QUESTION'

def test_unsupported_checklist_is_system_limitation():
    rows=qualify_checklist_results([{'question':'Проверить решение','status':'Не проверено системой','proof_kind':'UNSUPPORTED'}])
    assert rows[0]['verification_kind']=='SYSTEM_LIMITATION'
