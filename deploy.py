import os
import pandas
import utilities
from utilities import read_utils, app_utils

df = read_utils.load_pkdb_from_local_csv("pkdb.csv")
app_utils.deploy_datatable_app(df)
# app_utils.deploy_aggrid_app(df)
# app_utils.run_tutorial()

pass
