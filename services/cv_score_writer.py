from datetime import datetime
from services.supabase_client import supabase

def save_candidate_score(user_id, scores, institution_id=None, faculty=None):

    payload = {
        "user_id": user_id,
        "cv_quality_score": scores["cv_quality_score"],
        "cv_quality_band": scores["cv_quality_band"],
        "trust_index": scores["trust_index"],
        "trust_badge": scores["trust_badge"],
        "completeness_score": scores["completeness_score"],
        "role_alignment_score": scores["role_alignment_score"],
        "evidence_score": scores["evidence_score"],
        "specificity_score": scores["specificity_score"],
        "ats_score": scores["ats_score"],
        "professional_score": scores["professional_score"],
        "ers_score": scores["ers_score"],
        "institution_id": institution_id,
        "faculty": faculty,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    supabase.table("candidate_scores").insert(payload).execute()