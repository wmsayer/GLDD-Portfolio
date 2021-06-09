import time
import pandas as pd
import numpy as np

import itertools
from scipy import linalg
import matplotlib.pyplot as plt
import matplotlib as mpl

break_line = "/"*100
double_break = break_line + "\n" + break_line
sub_break = "|"*50

toolbar_width = 70
time_scale = {"sec": 1, "min": 60, "hr": 3600, "day": 24 * 3600}

color_iter = itertools.cycle(['navy', 'c', 'cornflowerblue', 'gold',
                              'darkorange'])


def print_time(old, old_total, message="", time_type="total", breaks=False):
    new = time.time()
    time_diff = new - old
    new_total = old_total + time_diff

    if breaks:
        print(break_line + "\n")

    if time_type == "diff":
        if message == "":
            print("Time Diff = %s seconds" % repr(time_diff))
        else:
            print(message + repr(time_diff) + " seconds")
    else:
        if message == "":
            print("Total Time = %s seconds" % repr(new_total))
        else:
            print(message + repr(new_total) + " seconds")

    if breaks:
        print(break_line + "\n")

    return new, new_total


def rename_trait_cols(df, name_dict, contains_all=True):
    """
    Simply renames column labels to match those defined in name_dict; keys = old names
    """
    if contains_all:
        df.rename(columns=name_dict, inplace=True)
    else:
        new_names = name_dict.copy()
        for col in df:
            if col not in new_names.keys():
                new_names[col] = col

        # df.rename(columns=name_dict, inplace=True)
        df.rename(columns=new_names, inplace=True)

    return df


def find_dt_col(feats):
    dt_col = ""

    for feat in feats:
        if "Date" in feat:
            dt_col = feat
            break

    return dt_col


def format_datetime(df):
    """Combines 'Date' and 'Time' columns into a single 'Datetime' column"""

    if 'DateTime' in df:
        df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %X')
        df.sort_values('DateTime', inplace=True)

    elif "Date" in df:
        temp_series = df.loc[:, 'Date'] + " " + df.loc[:, 'Time']
        df['DateTime'] = pd.to_datetime(temp_series, format='%m/%d/%Y %X')
        df.drop(columns='Date', inplace=True)
        df.drop(columns='Time', inplace=True)
        df.sort_values('DateTime', inplace=True)

    else:
        temp_series = df.loc[:, 'Date dd/mm/yyyy 27/1/1998'] + " " + df.loc[:, 'Time 24hr hh:mm:ss']

        df['DateTime'] = pd.to_datetime(temp_series, format='%m/%d/%Y %X')

        df.drop(columns='Date dd/mm/yyyy 27/1/1998', inplace=True)
        df.drop(columns='Time 24hr hh:mm:ss', inplace=True)
        df.sort_values('DateTime', inplace=True)

    # df.sort_values('DateTime', inplace=True)
    df.reset_index(inplace=True)
    df.drop(columns='index', inplace=True)
    df.reset_index(inplace=True)

    return df


def convert_time_delta(delta_t, unit):
    """

    :param delta_t: timedelta in nanoseconds
    :param unit:
    :return:
    """

    # print("Converting type:\n%s" % type(delta_t[0]))

    if type(delta_t[0]) == np.float64:
        return delta_t / 10**9 / time_scale[unit]

    if type(delta_t[0]) == np.timedelta64:
        return delta_t.astype('timedelta64[s]').astype(float) / time_scale[unit]

    # if type(delta_t[0]) == pd.timedelta64:
    #     return delta_t.astype('timedelta64[s]').astype(float) / time_scale[unit]

    print("////////////////////// ERROR: Time data type not recognized! /////////////////////////")


def get_time_interval(df):
    diff = np.median((df.loc[0:99, 'DateTime'].values - df.loc[1:100, 'DateTime'].values)).item()
    diff = abs(diff/1000000000)
    return diff


def check_clear_brackets(df):
    old_cols = df.columns
    new_cols = []

    for col in old_cols:

        if col[0] == "[":
            new_cols += [col.replace("[", "").replace("]", "")]
        else:
            new_cols += [col]

    df.columns = new_cols


def convert_to_sec(x):
    return x.total_seconds()


def plot_results(X, Y_, means, covariances, index, title):
    splot = plt.subplot(2, 1, 1 + index)

    for i, (mean, covar, color) in enumerate(zip(
            means, covariances, color_iter)):
        v, w = linalg.eigh(covar)
        v = 2. * np.sqrt(2.) * np.sqrt(v)
        u = w[0] / linalg.norm(w[0])
        # as the DP will not use every component it has access to
        # unless it needs it, we shouldn't plot the redundant
        # components.
        if not np.any(Y_ == i):
            continue
        plt.scatter(X[Y_ == i, 0], X[Y_ == i, 1], .8, color=color)

        # Plot an ellipse to show the Gaussian component
        angle = np.arctan(u[1] / u[0])
        angle = 180. * angle / np.pi  # convert to degrees
        ell = mpl.patches.Ellipse(mean, v[0], v[1], 180. + angle, color=color)
        ell.set_clip_box(splot.bbox)
        ell.set_alpha(0.5)
        splot.add_artist(ell)

    # plt.xlim(-9., 5.)
    # plt.ylim(-3., 6.)
    plt.xticks(())
    plt.yticks(())
    plt.title(title)


def plot_swing_data(opt_radii, x_c, y_c, thetas, x_0, y_0, centers_x, centers_y, og_center, extras):
    if opt_radii > 0:
        # plt.scatter(test_radii, err_dist, 0.1, color="blue")
        flat_x = centers_x.flatten()
        flat_y = centers_y.flatten()
        plt.scatter(flat_x, flat_y, 0.1, color="blue")

        cent_x = og_center[0] + np.arange(opt_radii - 400, opt_radii) * np.cos(np.radians(90 - og_center[2]))
        cent_y = og_center[1] + np.arange(opt_radii - 400, opt_radii) * np.sin(np.radians(90 - og_center[2]))
        plt.scatter(cent_x, cent_y, linewidths=0.2, marker="o", color="green")

        plt.scatter(x_0, y_0, linewidths=0.5, marker="o", color="red")

        plt.scatter(x_c, y_c, s=150, linewidths=0.1, marker="o", color="green")
        plt.scatter(x_c, y_c, s=100, linewidths=1.5, marker="x", color="gold")

        for k, ds in extras.items():
            plt.scatter(ds["x_vals"], ds["y_vals"], s=100, linewidths=1.5, marker=ds["shape"], color=ds["color"])

        exp_x = opt_radii * np.cos(thetas) + x_c
        exp_y = opt_radii * np.sin(thetas) + y_c
        # plt.scatter(exp_x, exp_y, linewidths=0.2, marker="o", color="black")

        plt.show()


def invert_dict(old_dict):
    inverted_dict = dict([(old_dict[n], n) for n in old_dict.keys()])
    return inverted_dict


def dict_items_to_list(x_dict):
    listed_items = [x_dict[n] for n in x_dict.keys()]
    return listed_items


def drop_idx_cols(df):
    check_cols = ['index', 'level_0', 'Unnamed: 0']
    for col in check_cols:
        if col in df.columns:
            df.drop(col, axis=1, inplace=True)
