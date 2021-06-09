from packages.General.Admin import *
import numpy as np
from packages.Connection.Connection import *
import math


def calc_relative(df, calc_info, default_val=-99):
    if "default" in calc_info.keys():
        default_val = calc_info["default"]

    final_data = default_val * np.ones(df.shape[0])
    record_int = math.ceil(calc_info["time"]/calc_info["frequency"])
    og_col = calc_info["column"]
    direction = {"forward": -1, "backward": 1}[calc_info["direction"]]

    # calculate difference in gyro position from "rec_int" number of records away (compare against single timestamp)
    future = pd.Series(df[og_col].values[record_int:])
    past = pd.Series(df[og_col].values[:-record_int])
    relative_df = direction * (future - past)

    if og_col == "Gyro":
        # check and adjust for jump in gyro value when dredge crosses true North (0/360)
        idx = pd.IndexSlice
        mask1 = relative_df > 300
        mask2 = relative_df < -300
        relative_df[idx[mask1]] -= 360
        relative_df[idx[mask2]] += 360

    # negative indicates
    if direction == 1:
        final_data[record_int:] = relative_df.values
    else:
        final_data[:-record_int] = relative_df.values

    return final_data


def calc_sog(df, calc_info, default_val=-99):

    if "default" in calc_info.keys():
        default_val = calc_info["default"]

    record_int = 1
    sog = default_val * np.ones(df.shape[0])
    col_dict = calc_info["columns"]

    curr_i = np.arange(record_int, df.shape[0])
    prev_i = np.arange(0, df.shape[0] - record_int)

    delta_x = df.loc[curr_i, col_dict["X"]].values - df.loc[prev_i, col_dict["X"]].values
    delta_y = df.loc[curr_i, col_dict["Y"]].values - df.loc[prev_i, col_dict["Y"]].values
    delta_l = np.sqrt(delta_x**2 + delta_y**2)

    delta_t = df.loc[curr_i, col_dict["DateTime"]].values - df.loc[prev_i, col_dict["DateTime"]].values
    delta_t = convert_time_delta(delta_t, calc_info["time_unit"])

    # check for time duplicates
    # idx = pd.IndexSlice
    # mask1 = delta_t == 0
    # mask2 = 2*np.ones(df.shape[0])
    # mask2[1:] = mask1
    # time_dups = mask2 == 1

    sog[curr_i] = delta_l / delta_t

    return sog


def calc_rate(df, calc_info, default_val=-99):

    if "default" in calc_info.keys():
        default_val = calc_info["default"]

    numrtr = calc_relative(df, calc_info, default_val=default_val)

    time_info = calc_info.copy()
    time_info.update({"column": "DateTime", "default": 10**9 * time_scale[time_info["time_unit"]]})
    denom = calc_relative(df, time_info)
    denom = convert_time_delta(denom, time_info["time_unit"])

    rate = numrtr / denom

    if calc_info["abs"]:
        rate = np.abs(rate)

    return rate


def calc_moving_avg(df, calc_info, default_val=-99):
    if "default" in calc_info.keys():
        default_val = calc_info["default"]

    final_data = default_val * np.ones(df.shape[0])
    # record_int = math.ceil(calc_info["time"]/calc_info["frequency"])
    og_col = calc_info["column"]

    last = df.shape[0] - 1
    prev = df.loc[: last - 2, og_col].values
    curr = df.loc[1:last - 1, og_col].values
    next = df.loc[2:last, og_col].values

    avg = (prev + curr + next) / 3

    final_data[1:last] = avg

    return final_data


def get_column_name(calc_info, i):
    col_name = "Calc_" + repr(i)

    if "name" in list(calc_info.keys()):
        return calc_info["name"]

    if "column" in list(calc_info.keys()):
        col_name = calc_info["type"] + "_" + calc_info["column"] + "_" + str.upper(
            calc_info["direction"][0]) + "_" + repr(calc_info["time"])

    if "columns" in list(calc_info.keys()):
        col_name = calc_info["type"] + "_" + calc_info["columns"]["X"][:-2] + "_" + str.upper(
            calc_info["direction"][0]) + "_" + repr(calc_info["time"])

    return col_name


def calc_columns(df, calc_dict):
    df.sort_values('DateTime', inplace=True)

    calc_func = {
        "SOG": calc_sog,
        "Relative": calc_relative,
        "MovAvg": calc_moving_avg,
        "Rate": calc_rate
    }

    new_names = []

    for calc_name, calc_info in calc_dict.items():
        col_name = get_column_name(calc_info, len(new_names))
        print('Calculating %s...' % col_name)
        df.loc[:, col_name] = calc_func[calc_info["type"]](df, calc_info)

        new_names += [col_name]

    return new_names