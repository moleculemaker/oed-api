create materialized view oed.ec_bar_chart as
 select 'kcat'::text as dataset,
    'EC ' || left(data_df_kcat.ec::text, 1) as ec_group,
    count(*) as count
   from oed.data_df_kcat
  group by left(data_df_kcat.ec::text, 1)
union all
 select 'Km'::text as dataset,
    'EC ' || left(data_df_km.ec::text, 1) as ec_group,
    count(*) as count
   from oed.data_df_km
  group by left(data_df_km.ec::text, 1)
union all
 select 'kcat/Km'::text as dataset,
    'EC ' || left(data_df_kcatkm.ec::text, 1) ec_group,
    count(*) as count
   from oed.data_df_kcatkm
  group by left(data_df_kcatkm.ec::text, 1);


create materialized view oed.kcat_ec_pie_chart as
 select 'kcat'::text AS dataset,
    'EC ' || left(ec::text, 1) as ec_class,
    count(*) AS count,
    round(count(*)::numeric * 100.0 / sum(count(*)) OVER (), 2) AS percentage
   from oed.data_df_kcat
  group by left(ec::text, 1)
  order by left(ec::text, 1);

create materialized view oed.kcatkm_ec_pie_chart AS
 select 'kcat/km'::text AS dataset,
    'EC '::text || left(ec::text, 1) as ec_class,
    count(*) AS count,
    round(count(*)::numeric * 100.0 / sum(count(*)) OVER (), 2) AS percentage
   from oed.data_df_kcatkm
  group by left(ec::text, 1)
  order by left(ec::text, 1);

create materialized view oed.km_ec_pie_chart AS
 select 'km'::text AS dataset,
    'EC ' || left(ec::text, 1) as ec_class,
    count(*) AS count,
    round(count(*)::numeric * 100.0 / sum(count(*)) OVER (), 2) AS percentage
   from oed.data_df_km
  group by left(ec::text, 1)
  order by left(ec::text, 1);


create materialized view oed.kinetic_summary AS
 select 'unique substrates'::text as metric,
    ( select count(distinct oed.data_df_kcat.substrate) as count
           from oed.data_df_kcat) as kcat_dataset,
    ( select count(distinct oed.data_df_km.substrate) as count
           from oed.data_df_km) as km_dataset,
    ( select count(distinct oed.data_df_kcatkm.substrate) as count
           from oed.data_df_kcatkm) as kcat_km_dataset
union all
 select 'unique organisms'::text as metric,
    ( select count(distinct oed.data_df_kcat.organism) as count
           from oed.data_df_kcat) as kcat_dataset,
    ( select count(distinct oed.data_df_km.organism) as count
           from oed.data_df_km) as km_dataset,
    ( select count(distinct oed.data_df_kcatkm.organism) as count
           from oed.data_df_kcatkm) as kcat_km_dataset
union all
 select 'unique uniprot ids'::text as metric,
    ( select count(distinct oed.data_df_kcat.uniprot) as count
           from oed.data_df_kcat) as kcat_dataset,
    ( select count(distinct oed.data_df_km.uniprot) as count
           from oed.data_df_km) as km_dataset,
    ( select count(distinct oed.data_df_kcatkm.uniprot) as count
           from oed.data_df_kcatkm) as kcat_km_dataset
union all
 select 'unique ec numbers'::text as metric,
    ( select count(distinct oed.data_df_kcat.ec) as count
           from oed.data_df_kcat) as kcat_dataset,
    ( select count(distinct oed.data_df_km.ec) as count
           from oed.data_df_km) as km_dataset,
    ( select count(distinct oed.data_df_kcatkm.ec) as count
           from oed.data_df_kcatkm) as kcat_km_dataset
union all
 select 'literature'::text as metric,
    ( select count(distinct oed.data_df_kcat.pubmedid) as count
           from oed.data_df_kcat) as kcat_dataset,
    ( select count(distinct oed.data_df_km.pubmedid) as count
           from oed.data_df_km) as km_dataset,
    ( select count(distinct oed.data_df_kcatkm.pubmedid) as count
           from oed.data_df_kcatkm) as kcat_km_dataset
union all
 select 'total entries'::text as metric,
    ( select count(*) as count
           from oed.data_df_kcat) as kcat_dataset,
    ( select count(*) as count
           from oed.data_df_km) as km_dataset,
    ( select count(*) as count
           from oed.data_df_kcatkm) as kcat_km_dataset;



