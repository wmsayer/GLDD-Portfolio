from packages.General.Admin import *
from packages.General.PhaseCleaning import main_phase_clean, check_phase_limits
from packages.General.FeatureCleaning import *
from packages.General.FeatureCalcs import *

import numpy as np
import pandas as pd
import math

idx = pd.IndexSlice
default_val = -99
phase_col = 'CSD_Phase'


def find_corners(df, time_int):
    """This function finds the timestamps where the dredge is located in a corner.
       This is done by comparing the current timestamp swing direction to the previous "rec_int" number of loggings.

    """

    print('Finding Corners...')

    # time rec_int in seconds to use for classification of corners
    class_int = 40

    # number of loggings to look back to grab previous swing direction
    rec_int = math.ceil(class_int/time_int)

    df['Corner'] = 'N'

    # ///////////////////////////////////////////////////////////////

    # build a matrix with "rec_int" number of columns in order to vectorize the comparison
    bool_check = pd.DataFrame(index=range(rec_int, df.shape[0]))
    for i in range(0, rec_int):
        col = 'Prev_%d' % i
        temp = df['Portswing'][rec_int - 1 - i: -(i + 1)].values
        bool_check[col] = temp

    check_all = bool_check.all(axis=1)
    check_any = bool_check.any(axis=1)

    curr_dir = df['Portswing'][rec_int:]
    temper = pd.Series([False] * rec_int)

    mask_p = np.logical_and(np.logical_not(curr_dir), check_all)
    temper_p = pd.concat([temper, mask_p], ignore_index=True)
    mask_s = np.logical_and(curr_dir, np.logical_not(check_any))
    temper_s = pd.concat([temper, mask_s], ignore_index=True)

    idx = pd.IndexSlice
    df.loc[idx[temper_p], 'Corner'] = 'P'
    df.loc[idx[temper_s], 'Corner'] = 'S'

    df.set_index(['Corner', 'index'], inplace=True, drop=False)


def classify_swings_and_corners(df):
    """This function finds the timestamps where the dredge is located in a corner.
           This is done by comparing the current timestamp swing direction to the previous "rec_int" number of loggings.

    """

    print('Classify Swings and Corners...')
    df[phase_col] = -1

    # classify as corner if:
    #       B45 or B20 and F45 both < 0 then Port Corner -- 3
    #       B45 or B20 and F45 both > 0 then Stbd Corner -- 4
    #       B20 < 0 and F45  > 0 then Port Swing -- 1
    #       B20 > 0 and F45  < 0 then Stbd Swing -- 2

    rg_cols = ["Relative_Gyro_B_45", "Relative_Gyro_B_20", "Relative_Gyro_F_45"]

    idx = pd.IndexSlice
    rg_mask = df.loc[:, rg_cols] > 0
    rg_b_mask = np.logical_or(rg_mask.loc[:, "Relative_Gyro_B_45"], rg_mask.loc[:, "Relative_Gyro_B_20"])

    # mask1 = np.logical_and(np.logical_not(rg_mask.loc[:, "Relative_Gyro_B_20"]), rg_mask.loc[:, "Relative_Gyro_F_45"])
    # mask2 = np.logical_and(rg_mask.loc[:, "Relative_Gyro_B_20"], np.logical_not(rg_mask.loc[:, "Relative_Gyro_F_45"]))
    mask1 = np.logical_not(rg_mask.loc[:, "Relative_Gyro_B_20"])
    mask2 = rg_mask.loc[:, "Relative_Gyro_B_20"]
    mask3 = np.logical_and(np.logical_not(rg_b_mask), np.logical_not(rg_mask.loc[:, "Relative_Gyro_F_45"]))
    mask4 = np.logical_and(rg_b_mask, rg_mask.loc[:, "Relative_Gyro_F_45"])

    df.loc[idx[mask1], phase_col] = 1
    df.loc[idx[mask2], phase_col] = 2
    df.loc[idx[mask3], phase_col] = 3
    df.loc[idx[mask4], phase_col] = 4


# # TODO: make faster
# def set_corner_swing_phases(df):
#     print('Setting corner/swing phases....')
#     df.set_index('Corner', inplace=True, drop=False)
#     df[phase_col] = -1
#     df['Swing_ID'] = -1
#
#     range_tol = 20*180/260/3.14159
#     ss_tol = 34
#     t_tol = np.timedelta64(1000 * 60, 'ms')
#
#     swing_id = 0
#     cs_dict = {3: 1, 4: 2}
#     idx = pd.IndexSlice
#
#     corners = df.loc[['P', 'S'], :]
#     corners = corners.sort_values('DateTime', inplace=False)
#     prev_t = 0
#     df.set_index('index', inplace=True, drop=False)
#
#     for index, row in corners.iterrows():
#         if row['Corner'] == 'P':
#             c_phase = 3
#         elif row['Corner'] == 'S':
#             c_phase = 4
#
#         # swing allocation
#         if prev_t != 0:
#             s_mask_pre = df.loc[:, 'DateTime'] > prev_t
#             s_mask_curr = df.loc[:, 'DateTime'] < row['DateTime']
#             s_mask_ch = df.loc[:, phase_col] == -1
#             s_mask = np.logical_and(s_mask_pre, s_mask_curr)
#             s_mask = np.logical_and(s_mask, s_mask_ch)
#
#             df.loc[idx[s_mask], phase_col] = cs_dict[c_phase]
#             # df.loc[idx[s_mask], 'Step_Size'] = row['Step_Size']
#             df.loc[idx[s_mask], 'Swing_ID'] = swing_id
#             swing_id += 1
#
#         prev_t = row['DateTime']
#
#         # tolerance for corner allocation
#         c_mask1 = df.loc[:, 'Swing_Speed'] < ss_tol
#         c_mask2 = df.loc[:, 'Cutter_SOG'] < ss_tol
#         c_mask = np.logical_or(c_mask1, c_mask2)
#         c_mask_r = abs(df.loc[:, 'Gyro'] - row['Gyro']) < range_tol
#         c_mask_t = abs(df.loc[:, 'DateTime'] - row['DateTime']) < t_tol
#         c_mask = np.logical_and(c_mask, c_mask_r)
#         c_mask = np.logical_and(c_mask, c_mask_t)
#         df.loc[idx[c_mask], phase_col] = c_phase
#         ind = row['index']
#
#         # ensures primary point gets included...may need to revisit
#         df.loc[ind - 2: ind, phase_col] = c_phase


def check_rel_gyro_delay(df):
    sensitivity = 1.75

    # print(df.loc[:, ["Relative_Gyro_B_45", "Relative_Gyro_F_45"]])
    # print(np.abs(df.loc[:, ["Relative_Gyro_B_45", "Relative_Gyro_F_45"]]))
    temp = np.abs(df.loc[:, ["Relative_Gyro_B_45", "Relative_Gyro_F_45"]])

    temp_mask = temp > 1

    # rgb_stat_vals = temp.loc[idx[temp_mask["Relative_Gyro_B_45"]], "Relative_Gyro_B_45"].values
    # rgb_limit = np.mean(rgb_stat_vals) - sensitivity * np.std(rgb_stat_vals)
    #
    # rgf_stat_vals = temp.loc[idx[temp_mask["Relative_Gyro_F_45"]], "Relative_Gyro_F_45"].values
    # rgf_limit = np.mean(rgf_stat_vals) - sensitivity * np.std(rgf_stat_vals)

    # rgb_vals = np.abs(df.loc[:, "Relative_Gyro_B_45"])
    # rgb_mask = rgb_vals < rgb_limit
    # rgf_vals = np.abs(df.loc[:, "Relative_Gyro_F_45"])
    # rgf_mask = rgf_vals < rgf_limit
    # rgd_mask = np.logical_and(rgb_mask, rgf_mask)

    rgd_radius = np.sqrt(df.loc[:, "Relative_Gyro_B_45"].values**2 + df.loc[:, "Relative_Gyro_F_45"].values**2)
    rgd_mask = rgd_radius < 2.5

    return rgd_mask


def recognize_delay(df):
    print('Recognizing delay from gauges...')
    score_col = "Delay_Score"

    # add Pump RPM
    delay_limits = {
                        'Ladder_Depth': [("<", 12, 1)],
                        'Velocity': [("<", 10, 2)],
                        'Density': [("<", 1.04, 1)],
                        # 'Swing_Speed': ("<", 10),
                        'Spud_SOG': [(">", 200, 2)],
                        "Rate_Gyro_B_5": [("<", 0.08, 1)],
                        # 'Cutter_SOG': ("<", 15),
                    }

    check_phase_limits(df, delay_limits, score_col)

    rgd_mask = check_rel_gyro_delay(df)
    df.loc[idx[rgd_mask], score_col] += 2

    score_mask = df[score_col] > 2

    df.loc[idx[score_mask], phase_col] = 5


def prepare_features(df, dredge_name, time_int):
    # time interval of data records in seconds
    if time_int == -1:
        time_int = get_time_interval(df)

    print("\tData record time interval: %s sec" % repr(time_int))

    calc_dict = {
                    'Cutter_SOG': {"type": "SOG", "name": "Cutter_SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
                                   "columns": {"X": "Cutter_X", "Y": "Cutter_Y", "DateTime": "DateTime"}},
                    'Spud_SOG': {"type": "SOG", "name": "Spud_SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
                                   "columns": {"X": "Spud_X", "Y": "Spud_Y", "DateTime": "DateTime"}},
                    # 'GPS_SOG': {"type": "SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
                    #              "columns": {"X": "Gps_X", "Y": "Gps_Y", "DateTime": "DateTime"}},
                    'RG_B20': {"type": "Relative", "time": 20, "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro"},
                    'RG_F20': {"type": "Relative", "time": 20, "frequency": 5, "direction": "forward", "default": default_val, "column": "Gyro"},
                    'RG_B45': {"type": "Relative", "time": 45, "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro"},
                    'RG_F45': {"type": "Relative", "time": 45, "frequency": 5, "direction": "forward", "default": default_val, "column": "Gyro"},
                    # 'RG_B60': {"type": "Relative", "time": 60, "frequency": time_int, "direction": "backward", "default": default, "column": "Gyro"},
                    # 'RG_F60': {"type": "Relative", "time": 60, "frequency": time_int, "direction": "forward", "default": default, "column": "Gyro"},
                    # 'MA_Density': {"type": "MovAvg", "time": 15, "frequency": 5, "direction": "center", "default": default_val, "column": "Density"},
                    # 'MA_Velocity': {"type": "MovAvg", "time": 15, "frequency": 5, "direction": "center", "default": default_val, "column": "Velocity"},
                    'Gyro_Rate': {"type": "Rate", "time": 5, "time_unit": "sec", "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro", "abs": True},
                }

    # time interval of data records in seconds
    if time_int == -1:
        time_int = get_time_interval(df)

    df['Frequency'] = time_int
    df['Frequency'] = df['Frequency'].astype(int)
    df['DredgeName'] = dredge_name

    df['Density'] = np.where(df['Density'].values < 1, 1, df['Density'].values)
    df['Velocity'] = np.where(df['Velocity'].values < 0, 0, df['Velocity'].values)

    remove_time_duplicates(df)
    final_features = calc_columns(df, calc_dict)

    remove_def_tups(df, final_features, default_val, drop=True)

    return df


def csd_recognize(dataf, dredge_name, time_int=-1):
    """
    This is the main function that takes in a single .mdb and allocates a CSD Phase to each time stamp
    :param dataf: pandas DataFrame of dredge data (i.e. loaded from IL20191104.mdb)
    :param delay_times: list of delay times
    :return: dataf: pd.DataFrame of dredge data with allocated CSD Phase

    This function assumes datetime is formatted properly into a single field and the DataFrame is ordered by datetime
    """

    print(sub_break + "\nClassifying data stream...")
    new_time = time.time()
    total_time = 0

    dataf = prepare_features(dataf, dredge_name, time_int)

    classify_swings_and_corners(dataf)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")

    recognize_delay(dataf)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")

    main_phase_clean(dataf, phase_col)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")

    # calc_delta_cl(dataf)
    # get_step_length_new(dataf)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")
    #
    # clean_ss_z(dataf)
    # new_time, total_time = print_time(new_time, total_time, "delta: ", "diff")

    new_time, total_time = print_time(new_time, total_time, "Total time to classify data: ", "total")

    return dataf


if __name__ == "__main__":
    print("\nSee \"Tests.py\" for tests.")


