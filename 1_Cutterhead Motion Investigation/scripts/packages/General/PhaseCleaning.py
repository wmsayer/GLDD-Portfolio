import numpy as np
from packages.Connection.Connection import *


idx = pd.IndexSlice


def check_phase_limits(df, phase_dict, score_col):
    df[score_col] = 0
    cols = list(phase_dict.keys())
    # df, temp_cols = calc_moving_avg(df, cols)

    for col in cols:
        for inst in phase_dict[col]:
            if inst[0] == ">":
                mask = df[col] > inst[1]
            else:
                mask = df[col] < inst[1]

            df.loc[idx[mask], score_col] += inst[2]


def phase_smooth(df, phase_col):

    last = df.shape[0] - 1
    prev = pd.Series(df.loc[: last - 3, phase_col].values)
    curr = pd.Series(df.loc[1:last - 2, phase_col].values)
    next = pd.Series(df.loc[2:last - 1, phase_col].values)
    next2 = pd.Series(df.loc[3:last, phase_col].values)

    check1 = curr.ne(prev)
    mask1 = prev.eq(next)
    mask2 = prev.eq(next2)

    check2 = curr.ne(prev)
    mask3 = curr.ne(next)
    mask4 = curr.ne(next2)

    mask_t1 = np.logical_or(mask1, mask2)
    mask_f1 = np.logical_and(mask_t1, check1)

    mask_t2 = np.logical_or(mask3, mask4)
    mask_f2 = np.logical_and(mask_t2, check2)

    mask_ff = np.logical_or(mask_f1, mask_f2)

    prev = list(df.loc[: last - 1, phase_col].values)
    prev_phase = pd.Series([-1] + prev, index=range(0, df.shape[0]))

    f_mask = np.array([False] + list(mask_ff.values) + [False, False])
    df.loc[idx[f_mask], phase_col] = prev_phase


def clear_delay_corners(df, phase_col):
    last = df.shape[0] - 1
    prev = pd.Series(df.loc[: last - 3, phase_col].values)
    curr = pd.Series(df.loc[1:last - 2, phase_col].values)
    next = pd.Series(df.loc[2:last - 1, phase_col].values)
    next2 = pd.Series(df.loc[3:last, phase_col].values)

    masks = []

    for c_phase in [3,4]:
        # prev_mask = prev > -2
        curr_mask = curr == c_phase
        next_mask = next == 5
        next2_mask = next2 == 5

        temp1 = np.column_stack((curr_mask, next_mask, next2_mask))
        masks.append(np.all(temp1, axis=1))

    temp = np.column_stack(tuple(masks))
    mask_ff = np.any(temp, axis=1)

    f_prev_mask = np.array(list(mask_ff) + [False, False, False])
    f_curr_mask = np.array([False] + list(mask_ff) + [False, False])

    df.loc[idx[f_prev_mask], phase_col] = 5
    df.loc[idx[f_curr_mask], phase_col] = 5


# TODO: If Delay exists in any of the considered timestamps, do not make any changes
def main_phase_clean(df, phase_col):
    print('Smoothing phases...')

    og = df[phase_col].copy()

    cleaning_sets = {
        "\tPhase Smooth": phase_smooth,
        # "Clear Delay Corners": clear_delay_corners,
        # "Clear Squiggle Corners":

    }

    for clean_type, clean_fn in cleaning_sets.items():

        check = True
        count = 0
        limit = 20

        # loop until no changes are made
        while check and count < limit:
            count += 1
            print('%s -- Iteration: %d' % (clean_type, count))
            clean_fn(df, phase_col)
            check = not og.equals(df.loc[:, phase_col])
            og = df[phase_col].copy()


if __name__ == "__main__":
    print("\nSee \"Tests.py\" for tests.")


