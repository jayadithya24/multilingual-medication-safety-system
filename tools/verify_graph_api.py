"""Read-only assertions against the running backend and live graph."""
import json
from urllib.parse import urlencode
from urllib.request import urlopen


def get(path, **query):
    with urlopen("http://127.0.0.1:8000" + path + ("?" + urlencode(query) if query else ""), timeout=20) as response:
        return json.load(response)


def main():
    graph = get("/neo4j/graph")
    assert graph["source"] == "neo4j", graph.get("source")
    ids = {n["node_id"] for n in graph["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in graph["links"])
    reference = get("/neo4j/search", term="Celecoxib")["results"][0]
    assert {i["drug_name"] for i in reference["interactions"]} >= {"Methotrexate", "Warfarin"}
    forward = get("/interaction", drug1="Ibuprofen", drug2="Methotrexate")["interaction"]
    reverse = get("/interaction", drug1="Methotrexate", drug2="Ibuprofen")["interaction"]
    assert forward == reverse and forward["review_required"]
    assert forward["source_severities"] == ["Moderate", "Severe"]
    assert get("/interaction", drug1="ibu", drug2="Methotrexate")["status"] == "not_found"
    live = get("/interaction", drug1="Celecoxib", drug2="Methotrexate")["interaction"]
    assert live["source"] == "neo4j" and live["severity"] == "Moderate"
    pair = get("/neo4j/interaction-graph", drug1="Ibuprofen", drug2="Methotrexate")
    interactions = [e for e in pair["links"] if e["relationship"] == "INTERACTS_WITH"]
    assert len(interactions) == 1 and interactions[0]["severity"] == "Review required"
    print(json.dumps({"source": graph["source"], "nodes": len(ids), "relationships": len(graph["links"]),
                      "reference_interactions": len(reference["interactions"]), "checks": "passed"}))


if __name__ == "__main__":
    main()
