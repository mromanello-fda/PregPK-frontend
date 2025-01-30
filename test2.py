import pickle
from data import complete_dataframe as GLOBAL_DF

atc_codes = GLOBAL_DF["atc_code"]

a10 = GLOBAL_DF[GLOBAL_DF["atc_code"] == "A10"]
a10