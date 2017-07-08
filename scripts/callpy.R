library(rPython)

python.exec("from impactcommon.math import averages")
python.assign('data', c(rep(0, 30), rep(1, 30)))
python.get("averages.translate(averages.BartlettAverager, 30, data)")

