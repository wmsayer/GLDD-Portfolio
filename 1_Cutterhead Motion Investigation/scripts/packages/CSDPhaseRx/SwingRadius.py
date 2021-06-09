import math
from ProdPackages.General.Admin import *
# import time
# import sys

idx = pd.IndexSlice


def calc_new_thetas(x_0, x_ref, y_0, y_ref):
    rel_x_0 = x_0 - x_ref
    rel_y_0 = y_0 - y_ref
    radius_sq = rel_x_0 ** 2 + rel_y_0 ** 2

    if type(radius_sq) == float and radius_sq == 0:
        return 0

    calc_cos = rel_x_0 / np.sqrt(radius_sq)
    theta_1 = np.arccos(calc_cos)
    rel_y_0 = np.where(rel_y_0 < 0, -1, 1)
    new_theta = theta_1 * rel_y_0

    return new_theta


def shape_gauge_reading(gauge_data, axes):
    data_cube = gauge_data.reshape(1, 1, gauge_data.shape[0], 1)
    data_cube = np.repeat(data_cube, axes[0], axis=0)
    data_cube = np.repeat(data_cube, axes[1], axis=1)
    data_cube = np.repeat(data_cube, axes[3], axis=3)
    return data_cube


def get_relative_heading(data_series):
    first_head = np.mean(data_series[0:2])
    mid_i = int(math.floor(data_series.shape[0]/2))
    mid_head = np.mean(data_series[mid_i - 1:mid_i + 1])
    last_head = np.mean(data_series[-3:-1])

    i = 0
    while not ((first_head < mid_head and mid_head < last_head) or (first_head > mid_head and mid_head > last_head)):
        data_series += 90
        data_series = data_series % 360

        first_head = np.mean(data_series[0:2])
        mid_head = np.mean(data_series[mid_i - 1:mid_i + 1])
        last_head = np.mean(data_series[-3:-1])

        i += 1

        if i > 5:
            return data_series, 0, False

    center_head = (first_head + last_head) / 2
    data_series -= center_head

    return data_series, center_head, True


def shift_gyro(df):
    gyro_shift = {
                    "IL": 0,
                    "CR": 0,
                    "TX": 0,
                    "OH": 0,
                    "AK": 0
                }

    dredge = df["DredgeName"][0]

    ts_shift = 3

    # shift heading one timestamp back
    # df["ShiftedHeading"] = np.array(list(df["Heading"].values[ts_shift:]) + list(df["Heading"].values[-ts_shift:])) + gyro_shift[dredge]

    # shift heading one timestamp forward
    # df["ShiftedHeading"] = np.array(list(df["Heading"].values[-ts_shift:]) + list(df["Heading"].values[0:-ts_shift])) + gyro_shift[dredge]

    df["ShiftedHeading"] = df["Heading"].values + gyro_shift[dredge]
    radius = np.sqrt((df["Gps_X"].values - df["CutterX"].values) ** 2 + (df["Gps_Y"].values - df["CutterY"].values) ** 2)

    # df["NewCutterX"] = radius * np.cos(np.radians(90 - df["ShiftedHeading"].values)) + df["Gps_X"].values
    # df["NewCutterY"] = radius * np.sin(np.radians(90 - df["ShiftedHeading"].values)) + df["Gps_Y"].values

    df["NewCutterX"] = df["CutterX"]
    df["NewCutterY"] = df["CutterY"]


def find_initial_swing_params(test_radii, cutter_sog, centers_x, centers_y):
    cutter_sog_rep = np.repeat(cutter_sog, test_radii.shape[1], axis=1)
    avgs_x = np.sum(centers_x * cutter_sog_rep, axis=0).reshape((1, -1)) / np.sum(cutter_sog, axis=0)
    avgs_y = np.sum(centers_y * cutter_sog_rep, axis=0).reshape((1, -1)) / np.sum(cutter_sog, axis=0)

    x_trans = np.repeat(avgs_x, centers_x.shape[0], axis=0)
    y_trans = np.repeat(avgs_y, centers_y.shape[0], axis=0)

    err_dist = np.sum(np.sqrt((centers_x - x_trans) ** 2 + (centers_y - y_trans) ** 2) * cutter_sog_rep, axis=0)
    min_e = np.amin(err_dist)
    opt_i = np.where(err_dist == min_e)[0].astype(int)

    if opt_i.shape[0] < 1:
        return {}

    og_opt = {
        "radius": test_radii[0, opt_i].astype(int).item(),
        "x_c": avgs_x[0, opt_i].astype(float).item(),
        "y_c": avgs_y[0, opt_i].astype(float).item()
    }

    return og_opt


def optimize_swing_params(buffer, step, og_opt, cutter_sog, rel_heading, x_i, y_i):
    curr_opt = og_opt.copy()
    rad_buffer = math.ceil(buffer)
    check = True
    count = 0

    # print("\tOG set: " + repr(curr_opt))

    while check and count < 3:
        final_radii = np.array(range(curr_opt["radius"] - rad_buffer, curr_opt["radius"] + rad_buffer)).reshape((1, 1, 1, -1))
        test_xc = np.arange(curr_opt["x_c"] - int(buffer), curr_opt["x_c"] + int(buffer), step).reshape((-1, 1))
        test_yc = np.arange(curr_opt["y_c"] - int(buffer), curr_opt["y_c"] + int(buffer), step).reshape((1, -1))

        test_xc = np.repeat(test_xc, test_yc.shape[0], axis=0)
        test_yc = np.repeat(test_yc, test_xc.shape[1], axis=1)

        delta_x_sheet = (x_i.reshape((1, -1)) - test_xc) ** 2
        delta_x_sheet = delta_x_sheet.reshape(delta_x_sheet.shape[0], 1, delta_x_sheet.shape[1])
        delta_y_sheet = (y_i.reshape((1, -1)) - test_yc.reshape((-1, 1))) ** 2
        delta_y_sheet = delta_y_sheet.reshape(1, delta_y_sheet.shape[0], delta_y_sheet.shape[1])
        delta_x_cube = np.repeat(delta_x_sheet, delta_y_sheet.shape[1], axis=1)
        delta_y_cube = np.repeat(delta_y_sheet, delta_x_sheet.shape[0], axis=0)

        meas_rad = np.sqrt(delta_x_cube + delta_y_cube)
        meas_rad = meas_rad.reshape((meas_rad.shape[0], meas_rad.shape[1], meas_rad.shape[2], 1))
        meas_rad = np.repeat(meas_rad, final_radii.shape[3], axis=3)

        cutter_sog_quad = shape_gauge_reading(cutter_sog, [test_xc.shape[0], test_yc.shape[1], 0, final_radii.shape[3]])
        rel_heading_quad = shape_gauge_reading(rel_heading, [test_xc.shape[0], test_yc.shape[1], 0, final_radii.shape[3]])

        rad_err = (meas_rad - final_radii) ** 2
        # rad_werr = np.sum(rad_err * cutter_sog_quad, axis=2) / np.sum(cutter_sog_quad, axis=2)

        err_shift = 0.65
        norm = 0.3
        abs_head = np.abs(rel_heading_quad)
        rel_head_quad_adj = np.abs(np.abs(abs_head/np.max(abs_head) - err_shift) - (1 - err_shift)) + norm
        rad_werr = np.sum(rad_err * cutter_sog_quad * rel_head_quad_adj, axis=2) / np.sum(cutter_sog_quad, axis=2)

        rad_rmse = np.sqrt(rad_werr)

        min_e = np.amin(rad_rmse)
        opt_i = np.where(rad_rmse == min_e)

        if opt_i[2].shape[0] < 1:
            return {}

        opt_rad_i = opt_i[2][0]
        opt_x_i = opt_i[0][0]
        opt_y_i = opt_i[1][0]

        curr_opt["radius"] = final_radii[0, 0, 0, opt_rad_i].astype(int).item()
        curr_opt["x_c"] = test_xc[opt_x_i, 0].astype(float).item()
        curr_opt["y_c"] = test_yc[0, opt_y_i].astype(float).item()

        loop_limit = 2
        check_rad = opt_rad_i < loop_limit or abs(final_radii.shape[3] - 1 - opt_rad_i) < loop_limit
        check_x = opt_x_i < loop_limit or abs(test_xc.shape[0] - 1 - opt_x_i) < loop_limit
        check_y = opt_y_i < loop_limit or abs(test_yc.shape[1] - 1 - opt_y_i) < loop_limit

        count += 1
        # print("\tOptimization %d: %s" % (count, repr(curr_opt)))

        mess = ""
        if check_rad:
            mess += ", radius"
        if check_x:
            mess += ", X coord"
        if check_y:
            mess += ", Y coord"
        if mess:
            # print("\t\t\t----- Loop again%s on edge -----" % mess)
            mess += ""

        check = check_rad or check_x or check_y

    return curr_opt, count


def write_opt_vals(swing_df, temp_swing, og_opt, new_opt, swing_i, center_head, x_i, y_i):
    opt_radius = new_opt["radius"]
    opt_x_c = new_opt["x_c"]
    opt_y_c = new_opt["y_c"]

    mask3 = swing_df["CSDPhaseLogId"] == swing_i
    swing_df.loc[idx[mask3], 'Radius'] = opt_radius
    swing_df.loc[idx[mask3], 'CenterX'] = opt_x_c
    swing_df.loc[idx[mask3], 'CenterY'] = opt_y_c

    wavg_bos = np.sum(temp_swing["LadderDepth"].values * temp_swing['Cutter_SOG'].values) / np.sum(
        temp_swing['Cutter_SOG'].values)
    swing_df.loc[idx[mask3], 'AvgBOS'] = wavg_bos
    swing_df.loc[idx[mask3], 'RadStdDev'] = np.std(np.sqrt(((x_i - opt_x_c) ** 2 + (y_i - opt_y_c) ** 2)) - opt_radius)
    swing_df.loc[idx[mask3], 'VertStdDev'] = np.std(temp_swing["LadderDepth"].values - wavg_bos)
    swing_df.loc[idx[mask3], 'OG_X'] = og_opt["x_c"]
    swing_df.loc[idx[mask3], 'OG_Y'] = og_opt["y_c"]
    swing_df.loc[idx[mask3], 'CenterHeading'] = center_head
    swing_df.loc[idx[mask3], 'Phi'] = np.degrees(calc_new_thetas(opt_x_c, og_opt["x_c"], opt_y_c, og_opt["y_c"]))


def drop_swing(rem_swings, e_type, dropped, swing_desc, mess_val=""):
    messages = {
        "DataPoints": "-------------- Skipping swing, not enough data points -----------------",
        "ShiftHeading": "//////////// Skipping swing, could not shift heading ///////////////////",
        "HeadingRange": "-------------- Skipping swing, heading range only %s -----------------" % mess_val,
        "Intersection": "////////////  Skipping swing, could not find intersection  ///////////////////",
        "SwingRadius": "-------------- Skipping swing, initial radius %s -----------------" % mess_val,
        "OptimizeFail": "//////////////  Skipping swing, could not optimize  ///////////////////"
    }

    # print("\t" + messages[e_type])

    if e_type in list(dropped.keys()):
        dropped[e_type].append(swing_desc)
    else:
        dropped[e_type] = [swing_desc]

    rem_swings -= 1
    return rem_swings


def calc_swing_radius_by_center(df, swing_df, testing=False):
    print(sub_break + "\nCalculating Swing Radii...")

    swing_df['Radius'] = 0
    swing_df['CenterX'] = 0
    swing_df['CenterY'] = 0
    swing_df['OG_X'] = -99
    swing_df['OG_Y'] = -99
    swing_df['CenterHeading'] = -99
    swing_df['Phi'] = -99

    shift_gyro(df)
    df["theta0"] = 90 - df["ShiftedHeading"]

    mask1 = df["CSDPhaseLogId"].isin(list(swing_df["CSDPhaseLogId"].values))
    fields = ['CutterX', 'CutterY', 'Heading', 'LadderDepth', 'CSDPhaseLogId', 'Cutter_SOG', 'Spud_X', 'Spud_Y',
              "Gps_X", "Gps_Y", "NewCutterX", "NewCutterY", "theta0", "ShiftedHeading"]
    swing_data = df.loc[idx[mask1], fields]

    swings = sorted(list(set(list(swing_data['CSDPhaseLogId'].values))))
    i = 0
    dropped = {}
    rem_swings = len(swings)
    num_opt = 0

    # setup toolbar
    # sys.stdout.write("%s" % (" " * toolbar_width))
    # sys.stdout.flush()
    # sys.stdout.write("\b" * (toolbar_width + 1))  # return to start of line, after '['
    # progress = 0

    for swing_i in swings:
        # time.sleep(0.1)
        # print("Calculating radius for CSDPhaseLogId = %d" % swing_i + " ({:.1f}%)".format(100*i/rem_swings))
        mask2 = swing_data["CSDPhaseLogId"] == swing_i
        temp_swing = swing_data.loc[idx[mask2], :]
        swing_desc = {"swing_i": swing_i}

        if temp_swing.shape[0] < 9:
            swing_desc["num_points"] = temp_swing.shape[0]
            e_type = "DataPoints"
            rem_swings = drop_swing(rem_swings, e_type, dropped, swing_desc)
            continue

        test_radii = np.array(range(0, 400)).reshape((1, -1))
        theta0 = temp_swing['theta0'].values.reshape((-1, 1))

        x_i = temp_swing['NewCutterX'].values.reshape((-1, 1))
        delta_x = test_radii * np.cos(theta0 / 180 * math.pi)
        centers_x = np.repeat(x_i, test_radii.shape[1], axis=1) - delta_x

        y_i = temp_swing['NewCutterY'].values.reshape((-1, 1))
        delta_y = test_radii * np.sin(theta0 / 180 * math.pi)
        centers_y = np.repeat(y_i, test_radii.shape[1], axis=1) - delta_y

        cutter_sog = temp_swing['Cutter_SOG'].values.reshape((-1, 1))
        rel_heading, center_head, found = get_relative_heading(temp_swing["ShiftedHeading"].values)

        if not found:
            e_type = "ShiftHeading"
            rem_swings = drop_swing(rem_swings, e_type, dropped, swing_desc)
            continue

        swing_desc["heading_range"] = abs(np.max(rel_heading) - np.min(rel_heading))

        if swing_desc["heading_range"] < 10:
            e_type = "HeadingRange"
            rem_swings = drop_swing(rem_swings, e_type, dropped, swing_desc, mess_val=repr(swing_desc["heading_range"]))
            continue

        og_opt = find_initial_swing_params(test_radii, cutter_sog, centers_x, centers_y)

        if not og_opt:
            e_type = "Intersection"
            rem_swings = drop_swing(rem_swings, e_type, dropped, swing_desc)
            continue

        swing_desc["init_radius"] = og_opt["radius"]

        if og_opt["radius"] < 100:
            e_type = "SwingRadius"
            rem_swings = drop_swing(rem_swings, e_type, dropped, swing_desc, mess_val=repr(swing_desc["init_radius"]))
            continue

        buffer = 5
        step = 0.25
        new_opt, its = optimize_swing_params(buffer, step, og_opt, cutter_sog, rel_heading, x_i, y_i)

        if not new_opt:
            e_type = "OptimizeFail"
            rem_swings = drop_swing(rem_swings, e_type, dropped, swing_desc)
            continue

        write_opt_vals(swing_df, temp_swing, og_opt, new_opt, swing_i, center_head, x_i, y_i)

        if testing:
            print("\nOptimization Results for CSDPhaseLogId = %d" % swing_i)
            print(meas_rad.shape)
            print(opt_i)

            diff = (math.sqrt((og_opt["x_c"] - new_opt["x_c"]) ** 2 + (og_opt["y_c"] - new_opt["y_c"]) ** 2),
                    new_opt["radius"] - og_opt["radius"])
            print("DeltaCenter = %s\nDeltaRadius = %s" % (repr(diff[0]), repr(diff[1])))

            new_thetas = calc_new_thetas(x_i, opt_x_c, y_i, opt_y_c)
            og_center = (x_c, y_c, center_head)

            extras = {
                       "Cutter_XY": {"color": "purple", "shape": "x", "x_vals": temp_swing['CutterX'].values, "y_vals": temp_swing['CutterY'].values},
                       "GPS_XY": {"color": "orange", "shape": "x", "x_vals": temp_swing['Gps_X'].values, "y_vals": temp_swing['Gps_Y'].values},
                       "Spud_XY": {"color": "orange", "shape": "x", "x_vals": temp_swing['Spud_X'].values, "y_vals": temp_swing['Spud_Y'].values},
                    }

            plot_swing_data(opt_radius, opt_x_c, opt_y_c, new_thetas, x_i, y_i, centers_x, centers_y, og_center, extras)

        num_opt += its
        i += 1

        # update the bar
        # curr_progress = math.ceil(i/rem_swings*toolbar_width)
        # inc_progress = curr_progress - progress

    #     if inc_progress > 0:
    #         sys.stdout.write("|"*inc_progress)
    #         progress = curr_progress
    #
    #     sys.stdout.flush()
    #
    # sys.stdout.write("]\n")  # this ends the progress bar

    num_dropped = 0
    print("\nSwing Radius Diagnostics:")
    for ev in list(dropped.keys()):
        print("\tCheck %s: %s" % (ev, dropped[ev]))
        print("\t\tTotal %s: %d" % (ev, len(dropped[ev])))
        num_dropped += len(dropped[ev])

    print("\n\tSwings Optimized: %d" % rem_swings)
    print("\tSwings Dropped: %d" % num_dropped)
    print("\tOptimizations: %d" % num_opt)
    print("\tOptimizations per swing: %s\n" % repr(num_opt/rem_swings))



def calc_swing_radius_by_xy_dist(x_0, test_xc, y_0, test_yc, final_radii, theta0):
    x_0_sheet = x_0.reshape((1, -1))
    # print(x_0_sheet[0, tp])
    x_0_sheet = np.repeat(x_0_sheet, test_xc.shape[0], axis=0)
    # print(x_0_sheet[tx, tp])
    x_0_sheet = x_0_sheet.reshape((test_xc.shape[0], 1, x_0.shape[0]))
    # print(x_0_sheet.shape)
    # print(x_0_sheet[tx, 0, tp])

    test_xc_sheet = np.repeat(test_xc, x_0.shape[0], axis=1)
    # print(test_xc_sheet[tx, tp])
    test_xc_sheet = test_xc_sheet.reshape((test_xc.shape[0], 1, x_0.shape[0]))
    # print(test_xc_sheet[tx, 0, tp])

    y_0_sheet = y_0.reshape((1, -1))
    # print(y_0_sheet[0, tp])
    y_0_sheet = np.repeat(y_0_sheet, test_yc.shape[1], axis=0)
    # print(y_0_sheet[ty, tp])
    y_0_sheet = y_0_sheet.reshape((1, test_yc.shape[1], y_0.shape[0]))
    # print(y_0_sheet.shape)
    # print(y_0_sheet[0, ty, tp])

    test_yc_sheet = np.repeat(test_yc, y_0.shape[0], axis=0)
    # print(test_yc_sheet[ty, tp])
    test_yc_sheet = test_yc_sheet.reshape((1, test_yc.shape[1], y_0.shape[0]))
    # print(test_yc_sheet[0, ty, tp])

    theta_sheet = theta0.reshape((1, -1))
    # print(theta_sheet[0, tp])
    theta_sheet = np.repeat(theta_sheet, test_xc.shape[0], axis=0)
    # print(theta_sheet[tx, tp])
    theta_sheet = theta_sheet.reshape((test_xc.shape[0], 1, theta0.shape[0]))
    # print(theta_sheet[tx, 0, tp])

    x_0_cube = np.repeat(x_0_sheet, y_0_sheet.shape[1], axis=1)
    # print(x_0_cube[tx, ty, tp])
    test_xc_cube = np.repeat(test_xc_sheet, y_0_sheet.shape[1], axis=1)
    # print(test_xc_cube[tx, ty, tp])

    y_0_cube = np.repeat(y_0_sheet, x_0_sheet.shape[0], axis=0)
    # print(y_0_cube[tx, ty, tp])
    test_yc_cube = np.repeat(test_yc_sheet, x_0_sheet.shape[0], axis=0)
    # print(test_yc_cube[tx, ty, tp])

    # theta_cube = np.repeat(theta_sheet, y_0_sheet.shape[1], axis=1)

    rel_x_0 = x_0_cube - test_xc_cube
    rel_y_0 = y_0_cube - test_yc_cube
    theta_cube = np.arccos(rel_x_0/np.sqrt(rel_x_0 ** 2 + rel_y_0 ** 2))
    rel_y_0 = np.where(rel_y_0 < 0, -1, 1)
    theta_cube = theta_cube * rel_y_0
    # print(theta_cube)

    final_radii = np.repeat(final_radii, test_xc.shape[0], axis=0)
    final_radii = np.repeat(final_radii, test_yc.shape[1], axis=1)
    final_radii = np.repeat(final_radii, x_0.shape[0], axis=2)

    # print(final_radii.shape)

    x_0_quad = x_0_cube.reshape((x_0_cube.shape[0], x_0_cube.shape[1], x_0_cube.shape[2], 1))
    x_0_quad = np.repeat(x_0_quad, final_radii.shape[3], axis=3)
    # print(x_0_quad.shape)
    # print(x_0_quad[tx, ty, tp, tr])

    test_xc_quad = test_xc_cube.reshape((test_xc_cube.shape[0], test_xc_cube.shape[1], test_xc_cube.shape[2], 1))
    test_xc_quad = np.repeat(test_xc_quad, final_radii.shape[3], axis=3)
    # print(test_xc_quad.shape)
    # print(test_xc_quad[tx, ty, tp, tr])

    y_0_quad = y_0_cube.reshape((y_0_cube.shape[0], y_0_cube.shape[1], y_0_cube.shape[2], 1))
    y_0_quad = np.repeat(y_0_quad, final_radii.shape[3], axis=3)
    # print(y_0_quad.shape)
    # print(y_0_quad[tx, ty, tp, tr])

    test_yc_quad = test_yc_cube.reshape((test_yc_cube.shape[0], test_yc_cube.shape[1], test_yc_cube.shape[2], 1))
    test_yc_quad = np.repeat(test_yc_quad, final_radii.shape[3], axis=3)
    # print(test_yc_quad.shape)
    # print(test_yc_quad[tx, ty, tp, tr])

    theta_quad = theta_cube.reshape((theta_cube.shape[0], theta_cube.shape[1], theta_cube.shape[2], 1))
    theta_quad = np.repeat(theta_quad, final_radii.shape[3], axis=3)
    # print(type(theta_quad))
    # print(theta_quad.shape)
    # print(theta_quad[tx, ty, tp, tr])

    # theta_quad_rad = theta_quad / 180 * math.pi

    # print(type(theta_quad_rad))
    # print(theta_quad_rad.shape)
    # print(theta_quad_rad[tx, ty, tp, tr]*180/math.pi)

    exp_x_quad = final_radii * np.cos(theta_quad) + test_xc_quad
    exp_y_quad = final_radii * np.sin(theta_quad) + test_yc_quad
    error_cube = (exp_x_quad - x_0_quad) ** 2 + (exp_y_quad - y_0_quad) ** 2

    rmse = np.sqrt(np.mean(error_cube, axis=2))
    print(error_cube.shape)
    print(rmse.shape)

    min_e = np.amin(rmse)
    print(min_e)

    opt_i = np.where(rmse == min_e)
    print(opt_i)
    print(opt_i[0].shape)
    print(opt_i[0][0])
    print(opt_i[1][0])
    print(opt_i[2][0])

    # if opt_i[0].shape > 1:

    opt_radii = final_radii[0, 0, 0, opt_i[2][-1]].astype(int).item()
    # print(opt_i.shape)
    # print(type(opt_radii))
    x_c = test_xc[opt_i[0][-1], 0].astype(float).item()
    y_c = test_yc[0, opt_i[1][-1]].astype(float).item()

    new_theta = theta_cube[opt_i[0][-1], opt_i[1][-1], :]