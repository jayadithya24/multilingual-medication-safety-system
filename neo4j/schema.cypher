// Constraints and indexes for the medication safety graph

// Unique constraints
CREATE CONSTRAINT drug_id_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.drug_id IS UNIQUE;
CREATE CONSTRAINT drug_name_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.drug_name IS UNIQUE;
CREATE CONSTRAINT generic_name_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.generic_name IS UNIQUE;
CREATE CONSTRAINT disease_id_unique IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_id IS UNIQUE;
CREATE CONSTRAINT disease_name_unique IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_name IS UNIQUE;
CREATE CONSTRAINT side_effect_name_unique IF NOT EXISTS FOR (s:SideEffect) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT interaction_id_unique IF NOT EXISTS FOR (i:Interaction) REQUIRE i.interaction_id IS UNIQUE;

// Indexes for faster lookups
CREATE INDEX drug_name_index IF NOT EXISTS FOR (d:Drug) ON (d.drug_name);
CREATE INDEX generic_name_index IF NOT EXISTS FOR (d:Drug) ON (d.generic_name);
CREATE INDEX disease_name_index IF NOT EXISTS FOR (d:Disease) ON (d.disease_name);