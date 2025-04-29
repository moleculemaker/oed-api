create schema oed;

create table oed.data_df_km as select * from le.data_df_km;

create table oed.data_df_kcat as select * from le.data_df_kcat;

create table oed.data_df_kcatkm as select * from le.data_df_kcatkm;

create index data_df_km_idx01 on oed.data_df_km (
    ec,
    substrate,
    organism,
    uniprot,
    enzymetype,
    ph,
    temperature,
    smiles
);

create index data_df_kcat_idx01 on oed.data_df_kcat (
    ec,
    substrate,
    organism,
    uniprot,
    enzymetype,
    ph,
    temperature,
    smiles
);

create index data_df_kcatkm_idx01 on oed.data_df_kcatkm (
    ec,
    substrate,
    organism,
    uniprot,
    enzymetype,
    ph,
    temperature,
    smiles
);
