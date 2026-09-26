CREATE CONSTRAINT medication_drug_id IF NOT EXISTS FOR (n:Drug) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT medication_disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT medication_side_effect_id IF NOT EXISTS FOR (n:SideEffect) REQUIRE n.id IS UNIQUE;
CREATE INDEX medication_drug_name IF NOT EXISTS FOR (n:Drug) ON (n.name);
CREATE INDEX medication_generic_name IF NOT EXISTS FOR (n:Drug) ON (n.generic_name);
