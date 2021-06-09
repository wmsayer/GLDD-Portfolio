from packages.General.Admin import *
import numpy as np
from packages.Connection.Connection import *

idx = pd.IndexSlice


def remove_time_duplicates(df):
    record_int = 1

    curr_i = np.arange(record_int, df.shape[0])
    prev_i = np.arange(0, df.shape[0] - record_int)

    delta_t = df.loc[curr_i, "DateTime"].values - df.loc[prev_i, "DateTime"].values
    delta_t = convert_time_delta(delta_t, "min")

    # check for time duplicates
    mask1 = delta_t == 0
    mask2 = 2*np.ones(df.shape[0])
    mask2[1:] = mask1

    dups = mask2 == 1
    in_vals = df.loc[idx[dups], :].index.values

    print("\tThere are %d time duplicates." % len(in_vals))
    df.drop(labels=in_vals, inplace=True)


def remove_def_tups(df, feats, default, drop=False):
    mask1 = df.loc[:, feats] != default
    # pd.set_option("display.max_rows", 20, "display.max_columns", 20)

    mask1 = mask1.all(axis=1)

    if drop:
        mask2 = np.logical_not(mask1)
        x = df.loc[idx[mask2], :]
        df.drop(labels=x.index.values, inplace=True)
        df.reset_index(inplace=True, drop=True)
    else:
        x = df.loc[idx[mask1], :]
        return x, mask1


def clean_ss_z(df):
    """This function looks at timestamps where we have been classified as swinging, but the SS reads less than 5fpm
       (possibly due to bug in PLC or sensor) the SS is the replaced with the Cutter_SOG"""

    print('Cleaning swing speeds...')

    df['Corrected_SS'] = df.loc[:, 'Swing_Speed']

    df.set_index('index', inplace=True, drop=False)
    mask_1 = df.loc[:, 'Swing_Speed'] < 5
    mask_2 = df.loc[:, 'CSD_Phase'] == 1
    mask_3 = df.loc[:, 'CSD_Phase'] == 2
    mask = np.logical_or(mask_2, mask_3)
    mask = np.logical_and(mask, mask_1)

    idx = pd.IndexSlice
    df.loc[idx[mask], 'Corrected_SS'] = df.loc[idx[mask], 'Cutter_SOG']


def clean_velocity(df):
    vel_dict = {"Port": {"velocity": "Port Velocity [fps]", "rpm": "Port Pump RPM"},
                "Stbd": {"velocity": "Stbd Velocity [fps]", "rpm": "Stbd Pump RPM"},
                }

    for filter_name, filter_dict in vel_dict.items():
        mask_vu = df[filter_dict["velocity"]] > 34
        mask_vl = df[filter_dict["velocity"]] < 0.25
        mask_rpm = df[filter_dict["rpm"]] < 10
        temp_mask = np.logical_or(mask_vu, mask_vl)
        temp_mask = np.logical_or(temp_mask, mask_rpm)
        df.loc[idx[temp_mask], filter_dict["velocity"]] = 0


def clean_density(df):
    dens_list = ["Port Density", "Stbd Density"]
    for col in dens_list:
        mask_d = df[col] < 1
        df.loc[idx[mask_d], col] = 1

    return df