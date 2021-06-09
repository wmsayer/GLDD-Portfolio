from packages.General.Admin import *
from packages.General.PhaseCleaning import main_phase_clean, check_phase_limits
from packages.General.FeatureCleaning import *
from packages.General.FeatureCalcs import *
import packages.Connection.LocalDBEnv as dbenv

idx = pd.IndexSlice
default_val = -99
state_col = 'TSHD_State'


def classify_pumpout(df):
    print('Classifying pumpout from gauges...')
    score_col = "PumpoutScore"

    # displacement is decreasing
    po_limits = {
                        'Speed [knots]': [("<", 3, 2), ("<", 1, 2)],
                        'Port Velocity [fps]': [(">", 2, 1)],
                        'Port Density': [(">", 1.04, 1)],
                        'Stbd Density': [(">", 1.04, 1)],
                        'Port Pump RPM': [(">", 10, 2)],
                        'Stbd Pump RPM': [(">", 10, 2)],
                        "Stbd Raw Draghead Depth": [("<", 12, 4)],
                        "Port Raw Draghead Depth": [("<", 12, 4)]
                    }

    check_phase_limits(df, po_limits, score_col)
    score_mask = df[score_col] > 13
    df.loc[idx[score_mask], state_col] = 4


def prepare_features(df, dredge_initials, time_int):
    # time interval of data records in seconds
    if time_int == -1:
        time_int = get_time_interval(df)

    print("\tData record time interval: %s sec" % repr(time_int))

    # calc_dict = {
    #                 'Cutter_SOG': {"type": "SOG", "name": "Cutter_SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
    #                                "columns": {"X": "Cutter_X", "Y": "Cutter_Y", "DateTime": "DateTime"}},
    #                 'Spud_SOG': {"type": "SOG", "name": "Spud_SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
    #                                "columns": {"X": "Spud_X", "Y": "Spud_Y", "DateTime": "DateTime"}},
    #                 # 'GPS_SOG': {"type": "SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
    #                 #              "columns": {"X": "Gps_X", "Y": "Gps_Y", "DateTime": "DateTime"}},
    #                 'RG_B20': {"type": "Relative", "time": 20, "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro"},
    #                 'RG_F20': {"type": "Relative", "time": 20, "frequency": 5, "direction": "forward", "default": default_val, "column": "Gyro"},
    #                 'RG_B45': {"type": "Relative", "time": 45, "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro"},
    #                 'RG_F45': {"type": "Relative", "time": 45, "frequency": 5, "direction": "forward", "default": default_val, "column": "Gyro"},
    #                 # 'RG_B60': {"type": "Relative", "time": 60, "frequency": time_int, "direction": "backward", "default": default, "column": "Gyro"},
    #                 # 'RG_F60': {"type": "Relative", "time": 60, "frequency": time_int, "direction": "forward", "default": default, "column": "Gyro"},
    #                 # 'MA_Density': {"type": "MovAvg", "time": 15, "frequency": 5, "direction": "center", "default": default_val, "column": "Density"},
    #                 # 'MA_Velocity': {"type": "MovAvg", "time": 15, "frequency": 5, "direction": "center", "default": default_val, "column": "Velocity"},
    #                 'Gyro_Rate': {"type": "Rate", "time": 5, "time_unit": "sec", "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro", "abs": True},
    #             }

    # time interval of data records in seconds
    if time_int == -1:
        time_int = get_time_interval(df)

    df['Frequency'] = time_int
    df['Frequency'] = df['Frequency'].astype(int)
    df['PlantNumber'] = dbenv.plant_num_dict[dredge_initials]
    df[state_col] = 0

    clean_velocity(df)
    clean_density(df)
    remove_time_duplicates(df)

    # final_features = calc_columns(df, calc_dict)
    # remove_def_tups(df, final_features, default_val, drop=True)

    return df


def set_stbd_velocity(df):
    mask_disc = df[state_col] == 4
    df.loc[idx[mask_disc], "Stbd Velocity [fps]"] = df.loc[idx[mask_disc], "Port Velocity [fps]"].values
    clean_velocity(df)


def tshd_recognize(dataf, dredge_initials, time_int=-1):
    """
    This is the main function that takes in a single .mdb and allocates a CSD Phase to each time stamp
    :param dataf: pandas DataFrame of dredge data (i.e. loaded from IL20191104.mdb)
    :param delay_times: list of delay times
    :return: dataf: pd.DataFrame of dredge data with allocated CSD Phase

    This function assumes datetime is formatted properly into a single field and the DataFrame is ordered by datetime
    """

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////////
    print(sub_break + "\nClassifying data stream...")
    new_time = time.time()
    total_time = 0

    dataf = prepare_features(dataf, dredge_initials, time_int)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")

    classify_pumpout(dataf)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")

    main_phase_clean(dataf, state_col)
    new_time, total_time = print_time(new_time, total_time, "\tdelta: ", "diff")

    set_stbd_velocity(dataf)
    new_time, total_time = print_time(new_time, total_time, "Total time to classify data: ", "total")

    return dataf