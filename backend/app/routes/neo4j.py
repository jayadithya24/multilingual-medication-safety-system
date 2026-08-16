from fastapi import APIRouter, HTTPException, Query

from backend.app.services.neo4j_service import (
    search_drug_by_text,
    get_drug_by_id,
    get_diseases,
    get_drugs_for_disease,
    get_knowledge_graph,
    get_interaction_graph,
)

router = APIRouter(
    prefix="/neo4j",
    tags=["neo4j"]
)


# =========================================================
# DRUG SEARCH
# =========================================================

@router.get("/search")
async def drug_search(
    term: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    results = search_drug_by_text(
        term,
        limit=limit
    )

    return {
        "results": results
    }


# =========================================================
# DRUG DETAILS
# =========================================================

@router.get("/drugs/{drug_id}")
async def drug_details(drug_id: str):

    result = get_drug_by_id(drug_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Drug not found"
        )

    return result


# =========================================================
# DISEASE LIST
# =========================================================

@router.get("/diseases")
async def disease_list():

    diseases = get_diseases()

    return {
        "status": "success",
        "diseases": diseases
    }


# =========================================================
# DRUGS FOR DISEASE
# =========================================================

@router.get("/diseases/{disease_name}/drugs")
async def disease_drugs(disease_name: str):

    drugs = get_drugs_for_disease(
        disease_name
    )

    return {
        "status": "success",
        "disease": disease_name,
        "drugs": drugs
    }


# =========================================================
# COMPLETE KNOWLEDGE GRAPH
# Used by Doctor Dashboard
# =========================================================

@router.get("/graph")
async def knowledge_graph():

    try:

        graph = get_knowledge_graph()

        return {
            "status": "success",
            "nodes": graph["nodes"],
            "links": graph.get(
                "links",
                graph.get("edges", [])
            )
        }

    except Exception as err:

        print(
            f"Neo4j graph lookup failed: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load knowledge graph"
        )


# =========================================================
# FOCUSED INTERACTION GRAPH
# Used by Drug Interaction page
# =========================================================

@router.get("/interaction-graph")
async def interaction_graph(
    drug1: str = Query(..., min_length=1),
    drug2: str = Query(..., min_length=1)
):

    try:

        graph = get_interaction_graph(
            drug1,
            drug2
        )

        return {
            "status": "success",
            "nodes": graph["nodes"],
            "links": graph["links"],
            "disease": graph.get("disease"),
            "selected_drugs": graph.get("selected_drugs", [])
        }

    except Exception as err:

        print(
            f"Neo4j interaction graph lookup failed: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load interaction graph"
        )