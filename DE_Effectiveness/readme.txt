1) Metadata error rate: how many metadata checks failed compared to how many were actually tested
 
2) Key error rate : how many key mismatches happened between source and target records
 
3) Data comparison error rate: overall data comparison quality, combining three types of data-level errors:
 
differences in actual data values
number of columns that failed comparison
errors from data-quality tests
 
4) Error rate : This is the overall error rate. It takes the highest of the above three as the final error score
 
5) Num of test: how many test runs exist for that project + table

This DE Effectiveness score includes the below:
 
Early system Behaviour (Later runs would include fixes, improvements, or re-runs)
Averaging only the first half of runs gives a more stable representation of historical error rate

Filter Logic
If there’s only one test → include it.
If there are multiple tests → include o
