
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