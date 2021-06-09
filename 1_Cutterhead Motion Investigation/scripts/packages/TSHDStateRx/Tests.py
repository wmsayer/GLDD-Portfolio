from packages.TSHDStateRx import ClassifyState
from packages.General import Admin
from packages.Connection import Connection
from packages.Connection.SQLapi.SQLAdmin import build_insert_query
# from Project.PredictiveMaintenance import clean_liberty
import numpy as np
import pandas as pd
import math


def test_combine_csv():
    root_path = "C:\\Users\\WSayer\\Desktop\\Productions\\Job Tracking\\72761 Jupiter Island\\ProjectDB\\PLCData"
    read_path = root_path + "\\Daily"
    write_path = root_path + "\\PLCDataMaster.csv"
    f_type = ".csv"
    df = Connection.combine_data_from_dir(read_path, f_type, dir_contains="", file_contains="", narrate=False, header='infer')
    print(df)
    Admin.format_datetime(df)

    df = ClassifyState.tshd_recognize(df, "LI")
    df.to_csv(write_path, index=False)


if __name__ == "__main__":
    test_combine_csv()
