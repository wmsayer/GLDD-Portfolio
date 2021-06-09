from packages.Connection.Connection import *
from packages.General.Admin import *
from packages.TSHDStateRx.ClassifyState import tshd_recognize
import packages.Connection.LocalDBEnv as dbenv
from itertools import dropwhile
import csv


def clean_read_pro(filename):
    new_file = clean_pro_file(filename)
    return read_csv(new_file)


def clean_pro_file(file):
    f_name = get_filename(file)
    w_file = update_file_dir(file, f_name)

    with open(w_file, 'w', newline='') as write_file:
        writer = csv.writer(write_file)
        with open(file, 'r') as fh:
            for curline in dropwhile(is_bad_line, fh):
                if not is_bad_line(curline):
                    currow = curline.split(",")
                    currow[-1] = currow[-1][:-1]
                    writer.writerow(currow)
    return w_file


def is_bad_line(s):
    good = False
    good_vals = ["Time", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    for val in good_vals:
        good = good or s.startswith(val)

    return not good


def get_filename(file):
    file_name = file.split("\\")[-1].split(".")[0]

    if file_name[:2] == "LB":
        file_name = "LI" + file_name[2:]

    return file_name


def read_csv(file):
    raw_df = pd.read_csv(file, skipinitialspace=True)
    format_datetime(raw_df)
    return raw_df
