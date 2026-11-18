# Human benchmark, step 2: REML random-effects model across the 36 ML1 sites (metafor), Q-profile CI for tau.
# Input : runs/human-ml1/site_effects.csv   Output: runs/human-ml1/metafor_results.json
# Run   : & "C:\Program Files\R\R-4.5.2\bin\Rscript.exe" analysis/human_ml1/metafor_human.R
lib <- file.path(Sys.getenv("USERPROFILE"), "R", "win-library", "4.5")
.libPaths(c(lib, .libPaths()))
suppressMessages(library(metafor))
cat("metafor", as.character(packageVersion("metafor")), " R", R.version.string, "\n")
root <- normalizePath(".")
se <- read.csv(file.path(root, "runs", "human-ml1", "site_effects.csv"), stringsAsFactors = FALSE)
res <- list()
for (key in unique(paste(se$paradigm, se$metric, sep = "/"))) {
  p <- strsplit(key, "/")[[1]]
  d <- se[se$paradigm == p[1] & se$metric == p[2], ]
  fit <- rma(yi = d$d, vi = d$v, method = "REML")
  ci <- confint(fit)   # Q-profile intervals for tau^2, tau, I^2, H^2
  res[[key]] <- list(
    paradigm = p[1], metric = p[2], k = fit$k,
    mu = as.numeric(fit$beta), mu_se = fit$se, mu_ci = c(fit$ci.lb, fit$ci.ub),
    tau2 = fit$tau2, tau = sqrt(fit$tau2),
    tau_ci_qprofile = sqrt(pmax(0, ci$random["tau^2", c("ci.lb", "ci.ub")])),
    I2 = fit$I2, I2_ci_qprofile = as.numeric(ci$random["I^2(%)", c("ci.lb", "ci.ub")]),
    Q = fit$QE, Q_df = fit$k - 1, Q_p = fit$QEp)
  cat(sprintf("%-10s %-9s k=%d mu=%.3f tau=%.3f [%.3f, %.3f] I2=%.1f Q=%.1f p=%.3f\n",
              p[1], p[2], fit$k, as.numeric(fit$beta), sqrt(fit$tau2),
              res[[key]]$tau_ci_qprofile[1], res[[key]]$tau_ci_qprofile[2], fit$I2, fit$QE, fit$QEp))
}
# minimal JSON writer (no jsonlite dependency)
tojson <- function(x) {
  if (is.list(x)) {
    if (!is.null(names(x))) return(paste0("{", paste0('"', names(x), '":', vapply(x, tojson, ""), collapse = ","), "}"))
    return(paste0("[", paste(vapply(x, tojson, ""), collapse = ","), "]"))
  }
  if (is.character(x) && length(x) == 1) return(paste0('"', x, '"'))
  if (length(x) == 1) return(format(x, digits = 10))
  paste0("[", paste(format(x, digits = 10), collapse = ","), "]")
}
writeLines(tojson(res), file.path(root, "runs", "human-ml1", "metafor_results.json"))
cat("sessionInfo\n"); print(sessionInfo()$R.version$version.string)
