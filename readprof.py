import pstats
p = pstats.Stats('prof')
p.strip_dirs().sort_stats('time').print_stats(10)
raw_input()
