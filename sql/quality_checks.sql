CREATE OR REPLACE TABLE quality.check_results AS
WITH checks AS (
    SELECT 'Q01_encounter_key_unique' AS check_name, (SELECT COUNT(*) - COUNT(DISTINCT encounter_id) FROM core.fact_encounter) AS failures
    UNION ALL SELECT 'Q02_psu_key_unique', (SELECT COUNT(*) - COUNT(DISTINCT psu_id) FROM core.dim_psu)
    UNION ALL SELECT 'Q03_psu_fk_valid', (SELECT COUNT(*) FROM core.fact_encounter e LEFT JOIN core.dim_psu p USING(psu_id) WHERE p.psu_id IS NULL)
    UNION ALL SELECT 'Q04_redirect_domain', (SELECT COUNT(*) FROM core.fact_encounter WHERE redirect_flag NOT IN (0,1) OR redirect_flag IS NULL)
    UNION ALL SELECT 'Q05_attained_domain', (SELECT COUNT(*) FROM core.fact_encounter WHERE attained_flag NOT IN (0,1) OR attained_flag IS NULL)
    UNION ALL SELECT 'Q06_positive_weight', (SELECT COUNT(*) FROM core.fact_encounter WHERE weight <= 0 OR weight IS NULL OR NOT ISFINITE(weight))
    UNION ALL SELECT 'Q07_service_nonempty', (SELECT COUNT(*) FROM core.fact_encounter WHERE service_type IS NULL OR TRIM(service_type)='')
    UNION ALL SELECT 'Q08_region_nonempty', (SELECT COUNT(*) FROM core.fact_encounter WHERE region IS NULL OR TRIM(region)='')
    UNION ALL SELECT 'Q09_stratum_nonempty', (SELECT COUNT(*) FROM core.fact_encounter WHERE stratum_id IS NULL OR TRIM(stratum_id)='')
    UNION ALL SELECT 'Q10_encounters_exist', CASE WHEN (SELECT COUNT(*) FROM core.fact_encounter) > 0 THEN 0 ELSE 1 END
    UNION ALL SELECT 'Q11_registry_exists', CASE WHEN (SELECT COUNT(*) FROM core.dim_psu) > 0 THEN 0 ELSE 1 END
    UNION ALL SELECT 'Q12_two_redirect_groups', CASE WHEN (SELECT COUNT(DISTINCT redirect_flag) FROM core.fact_encounter)=2 THEN 0 ELSE 1 END
    UNION ALL SELECT 'Q13_mart_rate_bounds', (SELECT COUNT(*) FROM mart.attainment_summary WHERE weighted_attainment_rate < 0 OR weighted_attainment_rate > 1)
    UNION ALL SELECT 'Q14_weight_reconciliation', CASE WHEN ABS((SELECT SUM(weighted_total) FROM mart.attainment_summary) - (SELECT SUM(weight) FROM core.fact_encounter)) < 1e-10 THEN 0 ELSE 1 END
    UNION ALL SELECT 'Q15_design_match', (SELECT COUNT(*) FROM core.fact_encounter e JOIN core.dim_psu p USING(psu_id) WHERE e.region<>p.region OR e.stratum_id<>p.stratum_id)
)
SELECT check_name, failures, CASE WHEN failures=0 THEN 'PASS' ELSE 'FAIL' END AS status FROM checks;
