from fastapi import APIRouter, HTTPException, Query
from backend.app.services.medicine_service import _load_dataset

from backend.app.services.neo4j_service import (
    search_drug_by_text, get_drug_by_id, get_diseases,
    get_drugs_for_disease, get_knowledge_graph, get_interaction_graph, get_related_graph,
)

router = APIRouter(prefix="/neo4j", tags=["neo4j"])


@router.get("/search")
def drug_search(term: str = Query(..., min_length=1),
                limit: int = Query(10, ge=1, le=50), lang: str = Query("en")):
    return {"results": search_drug_by_text(term, limit=limit, lang=lang)}


@router.get("/drugs/{drug_id}")
def drug_details(drug_id: str):
    result = get_drug_by_id(drug_id)
    if not result:
        raise HTTPException(status_code=404, detail="Drug not found")
    return result


@router.get("/diseases")
def disease_list(lang: str = "en"):
    data = _load_dataset(lang)
    diseases = sorted(set(data["disease"].astype(str))) if data is not None else []
    return {"status": "success", "diseases": diseases, "lang": lang,
            "disease_count": len(diseases),
            "medicine_count": int(data["drug_name"].nunique()) if data is not None else 0}


@router.get("/diseases/{disease_name:path}/drugs")
def disease_drugs(disease_name: str, lang: str = "en"):
    return {"status": "success", "disease": disease_name,
            "lang": lang, "drugs": get_drugs_for_disease(disease_name, lang)}


@router.get("/graph")
def knowledge_graph():
    try:
        graph = get_knowledge_graph()
        return {"status": "success", "nodes": graph["nodes"],
                "links": graph.get("links", graph.get("edges", [])),
                "source": graph.get("source", "unknown")}
    except Exception as err:
        raise HTTPException(status_code=503, detail="Knowledge graph is unavailable. No graph data could be loaded.") from err


@router.get("/interaction-graph")
def interaction_graph(drug1: str = Query(..., min_length=1),
                      drug2: str = Query(..., min_length=1)):
    try:
        graph = get_interaction_graph(drug1, drug2)
        return {"status": "success", "nodes": graph["nodes"],
                "links": graph["links"], "disease": graph.get("disease"),
                "selected_drugs": graph.get("selected_drugs", []),
                "source": graph.get("source", "unknown")}
    except Exception as err:
        raise HTTPException(status_code=503, detail="Interaction graph is unavailable. No interaction result could be verified.") from err


@router.get("/drug-graph")
def drug_graph(drug: str = Query(..., min_length=1)):
    try:
        return get_related_graph([drug])
    except Exception as err:
        raise HTTPException(status_code=503, detail="Medicine relationships are currently unavailable.") from err
