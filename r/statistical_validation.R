# Base R reference implementation: raw keyed tables in, no Python design/results read.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("usage: statistical_validation.R input_dir output_dir condition_limit")
input_dir <- args[1]
output_dir <- args[2]
condition_limit <- as.numeric(args[3])
if (!is.finite(condition_limit) || condition_limit <= 1) stop("invalid condition limit")
options(digits = 17, scipen = 999)
features <- c("intercept", "redirect_flag", "complexity", "assist_flag",
              "redirect_x_complexity", "service_B", "service_C")
read_table <- function(name, fields, key) {
  d <- read.csv(file.path(input_dir, name), colClasses = "character", check.names = FALSE)
  if (!identical(names(d), fields) || !nrow(d)) stop("input schema mismatch")
  if (anyNA(d) || any(d$synthetic_record != "true")) stop("missing values or synthetic marker")
  if (anyDuplicated(d[[key]]) || any(!grepl("^[A-Za-z0-9_-]{1,64}$", d[[key]]))) stop("invalid key")
  d
}
obs <- read_table("observations.csv", c("record_id", "psu_id", "stratum_id", "service_type",
                   "redirect_flag", "complexity", "assist_flag", "outcome", "synthetic_record"), "record_id")
weights <- read_table("weights.csv", c("record_id", "weight", "synthetic_record"), "record_id")
registry <- read_table("psu_registry.csv", c("psu_id", "stratum_id", "synthetic_record"), "psu_id")
if (!setequal(obs$record_id, weights$record_id)) stop("weight join not one-to-one")
if (!setequal(obs$psu_id, registry$psu_id)) stop("PSU inventory mismatch")
if (any(!grepl("^[A-Za-z0-9_-]{1,64}$", registry$stratum_id))) stop("invalid stratum")
if (any(table(registry$stratum_id) < 2)) stop("lonely PSU")
obs <- obs[order(obs$record_id), ]
raw_weight <- suppressWarnings(as.numeric(weights$weight[match(obs$record_id, weights$record_id)]))
if (any(!is.finite(raw_weight)) || any(raw_weight <= 0) || !is.finite(sum(raw_weight))) stop("invalid weight")
if (any(obs$stratum_id != registry$stratum_id[match(obs$psu_id, registry$psu_id)])) stop("stratum mismatch")
if (!setequal(obs$service_type, c("A", "B", "C"))) stop("service inventory mismatch")
for (name in c("redirect_flag", "complexity", "assist_flag", "outcome")) {
  obs[[name]] <- suppressWarnings(as.numeric(obs[[name]]))
  if (any(!is.finite(obs[[name]]))) stop("invalid numeric input")
}
if (any(!obs$redirect_flag %in% c(0, 1)) || any(!obs$assist_flag %in% c(0, 1))) stop("invalid flag")
a <- raw_weight / mean(raw_weight)
if (any(!is.finite(a)) || any(a <= 0)) stop("invalid normalized weights")
x <- cbind(intercept = 1, redirect_flag = obs$redirect_flag, complexity = obs$complexity,
           assist_flag = obs$assist_flag, redirect_x_complexity = obs$redirect_flag * obs$complexity,
           service_B = as.numeric(obs$service_type == "B"), service_C = as.numeric(obs$service_type == "C"))
y <- obs$outcome
n <- nrow(x)
p <- ncol(x)
wx <- x * sqrt(a)
singular_values <- svd(wx, nu = 0, nv = 0)$d
if (n <= p || min(singular_values) <= 0 || max(singular_values) / min(singular_values) > condition_limit) {
  stop("unsafe design rank/condition")
}
model <- stats::lm.wfit(x = x, y = y, w = a, tol = 1e-10, singular.ok = FALSE)
if (model$rank != p) stop("rank-deficient fit")
beta <- model$coefficients
prediction <- as.vector(x %*% beta)
residual <- y - prediction
scores <- x * (a * residual)
bread <- solve(crossprod(wx))
psus <- sort(unique(obs$psu_id))
u <- t(vapply(psus, function(key) colSums(scores[obs$psu_id == key, , drop = FALSE]), numeric(p)))
g <- length(psus)
influence <- u %*% t(bread)
cluster_cov <- crossprod(influence) * (g / (g - 1)) * ((n - 1) / (n - p))
stratum_cov <- matrix(0, p, p)
psu_strata <- registry$stratum_id[match(psus, registry$psu_id)]
for (stratum in sort(unique(psu_strata))) {
  z <- u[psu_strata == stratum, , drop = FALSE]
  centered <- sweep(z, 2, colMeans(z), "-")
  centered_influence <- centered %*% t(bread)
  stratum_cov <- stratum_cov + nrow(z) / (nrow(z) - 1) * crossprod(centered_influence)
}
cluster_cov <- (cluster_cov + t(cluster_cov)) / 2
stratum_cov <- (stratum_cov + t(stratum_cov)) / 2
if (any(!is.finite(c(beta, cluster_cov, stratum_cov, prediction, residual))) ||
    any(diag(cluster_cov) < 0) || any(diag(stratum_cov) < 0)) stop("invalid statistical output")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
write_result <- function(name, d) write.csv(d, file.path(output_dir, paste0("r_", name, ".csv")),
                                          row.names = FALSE, quote = FALSE, na = "NA")
write_result("design", data.frame(record_id = obs$record_id, psu_id = obs$psu_id, stratum_id = obs$stratum_id,
                                  raw_weight = raw_weight, analysis_weight = a, outcome = y, x, check.names = FALSE))
write_result("coefficients", data.frame(feature = features, estimate = beta,
                                        se_cluster = sqrt(diag(cluster_cov)), se_stratum = sqrt(diag(stratum_cov))))
cov_rows <- do.call(rbind, lapply(seq_len(p), function(i) {
  data.frame(row_feature = features[i], column_feature = features,
             cluster_cov = cluster_cov[i, ], stratum_cov = stratum_cov[i, ])
}))
write_result("covariance", cov_rows)
write_result("predictions", data.frame(record_id = obs$record_id, prediction = prediction, residual = residual))
diagnostics <- c(n = n, p = p, psus = g, strata = length(unique(obs$stratum_id)), rank = model$rank,
                 raw_weight_sum = sum(raw_weight), analysis_weight_sum = sum(a),
                 weighted_outcome_mean = sum(a * y) / sum(a),
                 kish_weight_concentration_n = sum(a)^2 / sum(a^2),
                 weighted_sse = sum(a * residual^2), condition_number = max(singular_values) / min(singular_values))
diagnostics <- diagnostics[order(names(diagnostics))]
write_result("diagnostics", data.frame(name = names(diagnostics), value = as.numeric(diagnostics)))
writeLines(R.version.string, file.path(output_dir, "r_version.txt"))
cat("R_STATISTICAL_VALIDATION=PASS\n")
