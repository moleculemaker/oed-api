-- Create the new table with reordered columns, prefixes instead of suffixes,
-- and a generated column for threshold delta
CREATE TABLE oed.oed_data (
    ec character varying,
    substrate character varying,
    organism character varying,
    uniprot character varying,
    enzymetype character varying,
    ph double precision,
    temperature double precision,
    smiles character varying,
    -- kcat group
    kcat_value double precision,
    kcat_pubmedid double precision,
    kcat_unit character varying,
    -- km group
    km_value double precision,
    km_pubmedid double precision,
    km_unit character varying,
    -- kcatkm group
    kcatkm_value double precision,
    kcatkm_pubmedid double precision,
    kcatkm_unit character varying,
    -- calculated threshold delta
    kcatkm_threshold_delta double precision GENERATED ALWAYS AS (
        CASE 
            WHEN kcat_value IS NOT NULL AND km_value IS NOT NULL AND kcatkm_value IS NOT NULL AND km_value != 0
            THEN ABS((kcat_value / km_value) - kcatkm_value)
            ELSE NULL
        END
    ) STORED
);

-- Add column comments
COMMENT ON COLUMN oed.oed_data.ec IS 'The Enzyme Commission Number, describing the type of reaction that is catalyzed by this enzyme. For examples of the EC Number hierarchy, please see the Open Enzyme Database Home Page, Statistics View.';
COMMENT ON COLUMN oed.oed_data.substrate IS 'The substrate (chemical compound) that is one of the reactants of the enzymatic reaction in question';
COMMENT ON COLUMN oed.oed_data.organism IS 'The organism (e.g. human, horse) in which the data for the enzymatic reaction was measured';
COMMENT ON COLUMN oed.oed_data.uniprot IS 'The unique accession number/identifier from the Uniprot database: https://www.uniprot.org/ for the enzyme catalyzing the reaction in question';
COMMENT ON COLUMN oed.oed_data.enzymetype IS 'Whether the enzyme catalyzing the reaction is "wild-type" (unmutated) or a mutant enzyme.';
COMMENT ON COLUMN oed.oed_data.ph IS 'The pH at which the data for the enzyme catalyzed reaction was collected.';
COMMENT ON COLUMN oed.oed_data.temperature IS 'The temperature (in degrees Celsius) at which the data for the enzyme catalyzed reaction was collected.';
COMMENT ON COLUMN oed.oed_data.smiles IS 'SMILES representation of the substrate chemical structure';
COMMENT ON COLUMN oed.oed_data.kcat_value IS 'The Michaelis-Menten catalytic rate constant (kcat) that was measured for the enzymatic reaction.';
COMMENT ON COLUMN oed.oed_data.kcat_pubmedid IS 'The PubMed Identifier (https://pubmed.ncbi.nlm.nih.gov/) for the experimental details from which the kcat data was collected.';
COMMENT ON COLUMN oed.oed_data.kcat_unit IS 'The unit of measurement for the kcat value';
COMMENT ON COLUMN oed.oed_data.km_value IS 'The Michaelis-Menten, Michaelis constant (in units of concentration - millimolar) for the enzymatic reaction.';
COMMENT ON COLUMN oed.oed_data.km_pubmedid IS 'The PubMed Identifier (https://pubmed.ncbi.nlm.nih.gov/) for the experimental details from which the Km data was collected.';
COMMENT ON COLUMN oed.oed_data.km_unit IS 'The unit of measurement for the Km value';
COMMENT ON COLUMN oed.oed_data.kcatkm_value IS 'The Michaelis-Menten catalytic efficiency (also known as specificity constant) in units of /second/mM for enzymatic reaction.';
COMMENT ON COLUMN oed.oed_data.kcatkm_pubmedid IS 'The PubMed Identifier (https://pubmed.ncbi.nlm.nih.gov/) for the experimental details from which the kcat/Km data was collected.';
COMMENT ON COLUMN oed.oed_data.kcatkm_unit IS 'The unit of measurement for the kcat/Km value';
COMMENT ON COLUMN oed.oed_data.kcatkm_threshold_delta IS 'Calculated absolute difference between the measured kcatkm_value and the computed value from kcat_value/km_value';

-- Insert data by joining all three tables on their common columns
-- Only include rows that exist in all three tables
INSERT INTO oed.oed_data (
    ec, substrate, organism, uniprot, enzymetype, ph, temperature, smiles,
    kcat_value, kcat_pubmedid, kcat_unit,
    km_value, km_pubmedid, km_unit,
    kcatkm_value, kcatkm_pubmedid, kcatkm_unit
)
SELECT 
    kcat.ec, 
    kcat.substrate, 
    kcat.organism, 
    kcat.uniprot, 
    kcat.enzymetype, 
    kcat.ph, 
    kcat.temperature, 
    kcat.smiles,
    -- kcat group
    kcat."KCAT VALUE" AS kcat_value, 
    kcat.pubmedid AS kcat_pubmedid,
    kcat.unit AS kcat_unit,
    -- km group
    km."KM VALUE" AS km_value,
    km.pubmedid AS km_pubmedid,
    km.unit AS km_unit,
    -- kcatkm group
    kcatkm."KCAT/KM VALUE" AS kcatkm_value,
    kcatkm.pubmedid AS kcatkm_pubmedid,
    kcatkm.unit AS kcatkm_unit
FROM 
    oed.data_df_kcat kcat
INNER JOIN 
    oed.data_df_km km
ON 
    kcat.ec = km.ec AND
    kcat.substrate = km.substrate AND
    kcat.organism = km.organism AND
    kcat.uniprot = km.uniprot AND
    kcat.enzymetype = km.enzymetype AND
    kcat.ph = km.ph AND
    kcat.temperature = km.temperature AND
    kcat.smiles = km.smiles
INNER JOIN 
    oed.data_df_kcatkm kcatkm
ON 
    kcat.ec = kcatkm.ec AND
    kcat.substrate = kcatkm.substrate AND
    kcat.organism = kcatkm.organism AND
    kcat.uniprot = kcatkm.uniprot AND
    kcat.enzymetype = kcatkm.enzymetype AND
    kcat.ph = kcatkm.ph AND
    kcat.temperature = kcatkm.temperature AND
    kcat.smiles = kcatkm.smiles;
