import numpy as np
import pandas as pd
from packages.General.Admin import *


def calc_delta_cl(df):
    i_back = 8
    last = df.shape[0] - 1

    back = pd.Series(list(df.loc[:(last - i_back), 'Cutter_Sta_on_CL'].values))
    forward = pd.Series(list(df.loc[i_back:last, 'Cutter_Sta_on_CL'].values))

    delta_CL = list((back - forward).values)
    df['DeltaCL'] = pd.Series(i_back*[0] + delta_CL, index=range(0, df.shape[0]))


# TODO: implement gradient descent to fit an arc to find radius and center point (seed length of dredge)
def get_step_length_old(df):
    print('Calculating step sizes...')
    df.set_index(['Corner', 'index'], inplace=True, drop=False)

    df['Step_Size'] = 0
    df['CornerId'] = -1

    sta_on_CL = df.loc[['P', 'S'], ['index', 'Cutter_Sta_on_CL']]
    temp1 = pd.Series(sta_on_CL['Cutter_Sta_on_CL'].values[:-1])
    temp2 = pd.Series(sta_on_CL['Cutter_Sta_on_CL'].values[1:])

    steps = temp2 - temp1
    direction = 1
    if (steps > 0).mean() < 0.5:
        direction = -1

    steps = steps * direction
    steps = pd.Series(list(steps.values) + [0], name='Step_Size', index=sta_on_CL['index'].values)
    df.set_index('index', inplace=True, drop=False)
    df.update(steps)
    df.set_index(['Corner', 'index'], inplace=True, drop=False)

    # clear out steps larger than 10ft and assign them a reset identification
    # assign corner_ids
    idx = pd.IndexSlice
    mask = abs(df.loc[:, 'Step_Size']) > 10
    df.loc[idx[mask], 'Corner'] = 'R'
    df.set_index(['Corner', 'index'], inplace=True, drop=False)

    cleaned_steps = df.loc[['P', 'S'], ['index', 'Cutter_Sta_on_CL']]
    corner_ids = pd.Series(range(0, cleaned_steps.shape[0]), name='CornerId', index=cleaned_steps['index'].values)
    df.set_index('index', inplace=True, drop=False)
    df.update(corner_ids)
    df.set_index(['Corner', 'index'], inplace=True, drop=False)


# TODO: implement gradient descent to fit an arc to find radius and center point (seed length of dredge)
def get_step_length_new(df):
    print('Calculating step sizes...')
    df.reset_index(inplace=True, drop=False)
    # df.set_index('index', inplace=True, drop=False)
    df.sort_values('DateTime', inplace=True)

    df['Step_Size'] = -99
    df['CornerId'] = -1

    idx = pd.IndexSlice
    mask3 = df.loc[:, 'CSD_Phase'] == 3
    mask4 = df.loc[:, 'CSD_Phase'] == 4
    mask = np.logical_or(mask3, mask4)

    cols = ["CSD_Phase", 'Cutter_Sta_on_CL', "index", "DateTime"]
    corners = pd.DataFrame(df.loc[idx[mask], cols].values, columns=cols)
    corners.reset_index(inplace=True, drop=False)
    # print(corners)

    prev = pd.DataFrame(corners.loc[:corners.shape[0] - 2, cols].values, columns=cols)
    # print(prev)
    curr = pd.DataFrame(corners.loc[1:, cols].values, columns=cols)
    # print(curr)

    dt_tol = 45
    delta_t = curr['DateTime'] - prev['DateTime']
    delta_t = convert_time_delta(delta_t.values, "sec")
    dt_mask = delta_t > dt_tol

    st_sz_tol = 15
    step_sizes = curr['Cutter_Sta_on_CL'] - prev['Cutter_Sta_on_CL']
    st_sz_mask = np.abs(step_sizes) < st_sz_tol

    dir_mask = np.not_equal(curr['CSD_Phase'], prev['CSD_Phase'])
    step_auth_mask = np.logical_and(dt_mask, st_sz_mask)

    # where meets delta_t and step size tolerance and opposite direction as previous
    step_mask1 = np.logical_and(dir_mask, step_auth_mask)
    step1_idx = curr.loc[idx[step_mask1], 'index'].values
    df.loc[step1_idx, "Step_Size"] = step_sizes[idx[step_mask1]].values
    df.loc[step1_idx, "CornerId"] = np.arange(0, step_sizes[idx[step_mask1]].shape[0])

    # where meets delta_t and step size tolerance, but same direction as previous
    step_mask2 = np.logical_and(np.logical_not(dir_mask), step_auth_mask).values
    # print(step_mask2)
    # print(step_mask2.shape)
    step_mask2 = np.array(list(step_mask2[1:]) + [False])

    step2_idx = curr.loc[idx[step_mask2], 'index'].values
    df.loc[step2_idx, "Step_Size"] = step_sizes[idx[step_mask2]].values


