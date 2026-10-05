CREATE OR REPLACE VIEW mart.attainment_summary AS
SELECT redirect_flag, COUNT(*) AS n, SUM(weight) AS weighted_total, SUM(weight * attained_flag) AS weighted_attained, SUM(weight * attained_flag) / NULLIF(SUM(weight), 0) AS weighted_attainment_rate
FROM core.fact_encounter GROUP BY redirect_flag;

CREATE OR REPLACE VIEW mart.service_summary AS
SELECT service_type, redirect_flag, COUNT(*) AS n, SUM(weight) AS weighted_total, SUM(weight * attained_flag) / NULLIF(SUM(weight), 0) AS weighted_attainment_rate
FROM core.fact_encounter GROUP BY service_type, redirect_flag;

CREATE OR REPLACE VIEW mart.psu_workload AS
SELECT p.region, p.stratum_id, p.psu_id, COUNT(e.encounter_id) AS encounter_count, SUM(e.weight) AS total_weight,
ROW_NUMBER() OVER (PARTITION BY p.stratum_id ORDER BY COUNT(e.encounter_id) DESC, p.psu_id) AS workload_rank_within_stratum
FROM core.dim_psu p LEFT JOIN core.fact_encounter e USING (psu_id)
GROUP BY p.region, p.stratum_id, p.psu_id;
