args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("usage: synthetic_parity.R input.csv output.csv")
input <- read.csv(args[1], stringsAsFactors = FALSE)
output <- args[2]
if (!all(input$redirect_flag %in% c(0,1))) stop("invalid redirect_flag")
if (!all(input$attained_flag %in% c(0,1))) stop("invalid attained_flag")
if (!all(is.finite(input$weight)) || any(input$weight <= 0)) stop("invalid weight")
overall <- sum(input$weight * input$attained_flag) / sum(input$weight)
rows <- lapply(sort(unique(input$redirect_flag)), function(g) {
  d <- input[input$redirect_flag == g,]
  total <- sum(d$weight)
  attained <- sum(d$weight * d$attained_flag)
  data.frame(redirect_flag=g,n=nrow(d),weighted_total=total,weighted_attained=attained,weighted_attainment_rate=attained/total,overall_weighted_attainment=overall)
})
result <- do.call(rbind, rows)
write.csv(result, output, row.names = FALSE, quote = FALSE)
cat("R_SYNTHETIC_SUMMARY_STATUS=PASS\n")
