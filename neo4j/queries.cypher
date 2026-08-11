// Cypher query templates for the medication safety system

// 1. Search drug by name (fuzzy)
MATCH (d:Drug)
WHERE toLower(d.drug_name) CONTAINS toLower($query)
   OR toLower(d.generic_name) CONTAINS toLower($query)
RETURN d LIMIT 10

// 2. Get full drug info
MATCH (d:Drug {drug_id: $drug_id})
OPTIONAL MATCH (d)-[:TREATS]->(dis:Disease)
OPTIONAL MATCH (d)-[:HAS_SIDE_EFFECT]->(se:SideEffect)
RETURN d, collect(dis) as diseases, collect(se) as side_effects

// 3. Check drug interactions (Doctor only)
MATCH (d1:Drug {drug_id: $drug1_id})-[r:INTERACTS_WITH]->(d2:Drug {drug_id: $drug2_id})
RETURN d1.drug_name, d2.drug_name, r.severity, r.description, r.disclaimer

// 4. All interactions for a drug
MATCH (d:Drug {drug_id: $drug_id})-[r:INTERACTS_WITH]->(d2:Drug)
RETURN d2.drug_name, r.severity, r.description, r.disclaimer
ORDER BY r.severity

// 5. All drugs for a disease
MATCH (d:Drug)-[:TREATS]->(dis:Disease {disease_id: $disease_id})
RETURN d.drug_id, d.drug_name, d.drug_class

// 6. Interaction severity lookup (multi-drug)
UNWIND $drug_ids AS drug_id
MATCH (d1:Drug {drug_id: drug_id})-[r:INTERACTS_WITH]->(d2:Drug)
WHERE d2.drug_id IN $drug_ids AND d1.drug_id < d2.drug_id
RETURN d1.drug_name, d2.drug_name, r.severity, r.description, r.disclaimer
ORDER BY
  CASE r.severity WHEN 'Severe' THEN 1 WHEN 'Moderate' THEN 2 ELSE 3 END

// 7. Drug contraindications
MATCH (d:Drug {drug_id: $drug_id})-[:CONTRAINDICATED_FOR]->(dis:Disease)
RETURN d.drug_name, collect(dis.disease_name)

// 8. Graph neighbourhood (Researcher)
MATCH (d:Drug {drug_id: $drug_id})-[r]-(connected)
RETURN d, r, connected LIMIT 50