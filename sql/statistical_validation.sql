-- Independent reconstruction from raw keyed inputs; never fit from a Python matrix.
CREATE OR REPLACE VIEW sql_design AS
SELECT o.record_id, o.psu_id, o.stratum_id, w.weight AS raw_weight,
       w.weight / (SELECT AVG(weight) FROM weights) AS analysis_weight, o.outcome,
       1.0 AS intercept, o.redirect_flag, o.complexity, o.assist_flag,
       o.redirect_flag * o.complexity AS redirect_x_complexity,
       CASE WHEN o.service_type = 'B' THEN 1.0 ELSE 0.0 END AS service_B,
       CASE WHEN o.service_type = 'C' THEN 1.0 ELSE 0.0 END AS service_C
FROM observations o JOIN weights w USING (record_id);

CREATE OR REPLACE VIEW expected_features AS
SELECT * FROM (VALUES ('intercept'), ('redirect_flag'), ('complexity'), ('assist_flag'),
                     ('redirect_x_complexity'), ('service_B'), ('service_C')) AS t(feature);

CREATE OR REPLACE VIEW reconstructed_predictions AS
SELECT x.record_id,
       x.intercept * (SELECT estimate FROM coefficients WHERE feature='intercept') +
       x.redirect_flag * (SELECT estimate FROM coefficients WHERE feature='redirect_flag') +
       x.complexity * (SELECT estimate FROM coefficients WHERE feature='complexity') +
       x.assist_flag * (SELECT estimate FROM coefficients WHERE feature='assist_flag') +
       x.redirect_x_complexity * (SELECT estimate FROM coefficients WHERE feature='redirect_x_complexity') +
       x.service_B * (SELECT estimate FROM coefficients WHERE feature='service_B') +
       x.service_C * (SELECT estimate FROM coefficients WHERE feature='service_C') AS prediction
FROM sql_design x;

CREATE OR REPLACE TABLE statistical_checks AS
WITH checks AS (
    SELECT 'S01_observation_keys' AS check_name,
           (SELECT COUNT(*) - COUNT(DISTINCT record_id) FROM observations) AS failures
    UNION ALL SELECT 'S02_weight_keys', (SELECT COUNT(*) - COUNT(DISTINCT record_id) FROM weights)
    UNION ALL SELECT 'S03_exact_weight_join',
        (SELECT COUNT(*) FROM observations o FULL OUTER JOIN weights w USING(record_id)
         WHERE o.record_id IS NULL OR w.record_id IS NULL)
    UNION ALL SELECT 'S04_registry_keys', (SELECT COUNT(*) - COUNT(DISTINCT psu_id) FROM psu_registry)
    UNION ALL SELECT 'S05_psu_nesting',
        (SELECT COUNT(*) FROM observations o LEFT JOIN psu_registry p USING(psu_id)
         WHERE p.psu_id IS NULL OR o.stratum_id IS NULL OR o.stratum_id <> p.stratum_id)
    UNION ALL SELECT 'S06_unused_registry_psus',
        (SELECT COUNT(*) FROM psu_registry p LEFT JOIN (SELECT DISTINCT psu_id FROM observations) o USING(psu_id)
         WHERE o.psu_id IS NULL)
    UNION ALL SELECT 'S07_no_lonely_psu',
        (SELECT COUNT(*) FROM (SELECT stratum_id FROM psu_registry GROUP BY stratum_id HAVING COUNT(*) < 2))
    UNION ALL SELECT 'S08_finite_positive_weights',
        (SELECT COUNT(*) FROM weights WHERE weight IS NULL OR NOT ISFINITE(weight) OR weight <= 0)
    UNION ALL SELECT 'S09_input_domains',
        (SELECT COUNT(*) FROM observations WHERE redirect_flag NOT IN (0,1) OR assist_flag NOT IN (0,1)
          OR redirect_flag IS NULL OR assist_flag IS NULL OR service_type NOT IN ('A','B','C')
          OR service_type IS NULL OR outcome IS NULL OR NOT ISFINITE(outcome)
          OR complexity IS NULL OR NOT ISFINITE(complexity))
    UNION ALL SELECT 'S10_design_row_inventory',
        (SELECT COUNT(*) FROM sql_design s FULL OUTER JOIN python_design p USING(record_id)
         WHERE s.record_id IS NULL OR p.record_id IS NULL) +
        (SELECT COUNT(*) - COUNT(DISTINCT record_id) FROM python_design)
    UNION ALL SELECT 'S11_feature_reconstruction',
        (SELECT COUNT(*) FROM sql_design s JOIN python_design p USING(record_id)
         WHERE p.intercept IS NULL OR p.redirect_flag IS NULL OR p.complexity IS NULL
          OR p.assist_flag IS NULL OR p.redirect_x_complexity IS NULL OR p.service_B IS NULL OR p.service_C IS NULL
          OR NOT ISFINITE(p.intercept) OR NOT ISFINITE(p.redirect_flag) OR NOT ISFINITE(p.complexity)
          OR NOT ISFINITE(p.assist_flag) OR NOT ISFINITE(p.redirect_x_complexity)
          OR NOT ISFINITE(p.service_B) OR NOT ISFINITE(p.service_C)
          OR ABS(s.intercept-p.intercept)>1e-12 OR ABS(s.redirect_flag-p.redirect_flag)>1e-12
          OR ABS(s.complexity-p.complexity)>1e-12 OR ABS(s.assist_flag-p.assist_flag)>1e-12
          OR ABS(s.redirect_x_complexity-p.redirect_x_complexity)>1e-12
          OR ABS(s.service_B-p.service_B)>1e-12 OR ABS(s.service_C-p.service_C)>1e-12)
    UNION ALL SELECT 'S12_weight_reconstruction',
        (SELECT COUNT(*) FROM sql_design s JOIN python_design p USING(record_id)
         WHERE p.raw_weight IS NULL OR p.analysis_weight IS NULL
          OR NOT ISFINITE(p.raw_weight) OR NOT ISFINITE(p.analysis_weight)
          OR ABS(s.raw_weight-p.raw_weight)>1e-12*GREATEST(1,ABS(s.raw_weight))
          OR ABS(s.analysis_weight-p.analysis_weight)>1e-12*GREATEST(1,ABS(s.analysis_weight)))
    UNION ALL SELECT 'S13_design_outcome_and_nesting',
        (SELECT COUNT(*) FROM sql_design s JOIN python_design p USING(record_id)
         WHERE p.psu_id IS NULL OR p.stratum_id IS NULL OR p.outcome IS NULL
          OR s.psu_id<>p.psu_id OR s.stratum_id<>p.stratum_id OR NOT ISFINITE(p.outcome)
          OR ABS(s.outcome-p.outcome)>1e-12)
    UNION ALL SELECT 'S14_weight_normalization',
        CASE WHEN ABS((SELECT SUM(analysis_weight) FROM python_design) -
                      (SELECT COUNT(*) FROM observations)) < 1e-10 THEN 0 ELSE 1 END
    UNION ALL SELECT 'S15_coefficient_inventory',
        (SELECT COUNT(*) FROM expected_features e FULL OUTER JOIN coefficients c USING(feature)
         WHERE e.feature IS NULL OR c.feature IS NULL) +
        (SELECT COUNT(*) - COUNT(DISTINCT feature) FROM coefficients) +
        (SELECT COUNT(*) FROM coefficients WHERE estimate IS NULL OR se_cluster IS NULL OR se_stratum IS NULL
          OR NOT ISFINITE(estimate) OR NOT ISFINITE(se_cluster)
          OR NOT ISFINITE(se_stratum) OR se_cluster<0 OR se_stratum<0)
    UNION ALL SELECT 'S16_prediction_inventory',
        (SELECT COUNT(*) FROM observations o FULL OUTER JOIN predictions p USING(record_id)
         WHERE o.record_id IS NULL OR p.record_id IS NULL) +
        (SELECT COUNT(*) - COUNT(DISTINCT record_id) FROM predictions) +
        (SELECT COUNT(*) FROM predictions WHERE prediction IS NULL OR residual IS NULL
          OR NOT ISFINITE(prediction) OR NOT ISFINITE(residual))
    UNION ALL SELECT 'S17_prediction_reconstruction',
        (SELECT COUNT(*) FROM reconstructed_predictions r JOIN predictions p USING(record_id)
         WHERE ABS(r.prediction-p.prediction)>1e-10*GREATEST(1,ABS(r.prediction)))
    UNION ALL SELECT 'S18_residual_reconciliation',
        (SELECT COUNT(*) FROM observations o JOIN predictions p USING(record_id)
         WHERE ABS(o.outcome-p.prediction-p.residual)>1e-10)
    UNION ALL SELECT 'S19_weighted_normal_equations',
        (SELECT COUNT(*) FROM (
            SELECT UNNEST([SUM(x.analysis_weight*p.residual*x.intercept),
                           SUM(x.analysis_weight*p.residual*x.redirect_flag),
                           SUM(x.analysis_weight*p.residual*x.complexity),
                           SUM(x.analysis_weight*p.residual*x.assist_flag),
                           SUM(x.analysis_weight*p.residual*x.redirect_x_complexity),
                           SUM(x.analysis_weight*p.residual*x.service_B),
                           SUM(x.analysis_weight*p.residual*x.service_C)]) AS score
            FROM sql_design x JOIN predictions p USING(record_id)) WHERE NOT ISFINITE(score) OR ABS(score)>1e-7)
    UNION ALL SELECT 'S20_covariance_inventory',
        (SELECT COUNT(*) FROM (SELECT a.feature AS row_feature, b.feature AS column_feature
                              FROM expected_features a CROSS JOIN expected_features b) e
         FULL OUTER JOIN covariance c USING(row_feature,column_feature)
         WHERE e.row_feature IS NULL OR c.row_feature IS NULL) +
        (SELECT COUNT(*) - COUNT(DISTINCT (row_feature,column_feature)) FROM covariance)
    UNION ALL SELECT 'S21_covariance_properties',
        (SELECT COUNT(*) FROM covariance c JOIN covariance t
          ON c.row_feature=t.column_feature AND c.column_feature=t.row_feature
         WHERE c.cluster_cov IS NULL OR c.stratum_cov IS NULL OR NOT ISFINITE(c.cluster_cov) OR NOT ISFINITE(c.stratum_cov)
          OR ABS(c.cluster_cov-t.cluster_cov)>1e-10 OR ABS(c.stratum_cov-t.stratum_cov)>1e-10
          OR (c.row_feature=c.column_feature AND (c.cluster_cov<0 OR c.stratum_cov<0)))
    UNION ALL SELECT 'S22_standard_error_reconciliation',
        (SELECT COUNT(*) FROM coefficients b JOIN covariance c ON b.feature=c.row_feature AND b.feature=c.column_feature
         WHERE ABS(b.se_cluster*b.se_cluster-c.cluster_cov)>1e-10
          OR ABS(b.se_stratum*b.se_stratum-c.stratum_cov)>1e-10)
    UNION ALL SELECT 'S23_weighted_mean_and_sse',
        CASE WHEN ABS((SELECT value FROM diagnostics WHERE name='weighted_outcome_mean') -
                      (SELECT SUM(analysis_weight*outcome)/SUM(analysis_weight) FROM sql_design)) < 1e-10
              AND ABS((SELECT value FROM diagnostics WHERE name='weighted_sse') -
                      (SELECT SUM(x.analysis_weight*p.residual*p.residual) FROM sql_design x JOIN predictions p USING(record_id))) < 1e-9
             THEN 0 ELSE 1 END
)
SELECT check_name, failures, CASE WHEN failures=0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks ORDER BY check_name;
