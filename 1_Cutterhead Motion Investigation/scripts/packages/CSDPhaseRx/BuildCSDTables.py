from packages.CSDPhaseRx import SwingRadius
# from AggregateStats import *
from packages.General.Admin import *
from datetime import datetime
import pandas as pd
import numpy as np

# import time
# import sys


db_schema = {
            'CutterRecord': {"index": 'CutterRecordId', "foreign_keys": [], "time": {"start": 'DateTime', "end": 'DateTime'},
                             "attributes": ['CutterRecordId', 'DredgeId', 'DateTime', 'CutterX', 'CutterY', 'TideHeight', 'CenterLineStation', 'CutterStation', 'CutterRange', 'CarriagePosition', 'LadderDepth', 'Heading', 'Velocity', 'Density', 'UnderWaterPumpPower', 'CutterCurrent', 'CutterSpeed', 'PortSwingCurrent', 'StbdSwingCurrent', 'SuctionPressure', 'DischargePressure', 'PortPumpSpeed', 'StbdPumpSpeed', 'SwingSpeed', 'InSituDensity', 'WaterDensity', 'Booster1Pump1Load', 'Booster1Pump1IncomingPressure', 'Booster1Pump1DischargePressure', 'Booster1Pump1Speed', 'Booster2Pump1Load', 'Booster2Pump1IncomingPressure', 'Booster2Pump1DischargePressure', 'Booster2Pump1Speed', 'BeforeDredgeDepth'],
                             },
            'CSDCut': {"index": 'CSDCutId', "foreign_keys": [],
                       "attributes": ['CSDCutId', 'BorrowId', 'mCL', 'bCL'],
                       },
            'CSDPhaseLog': {"index": 'CSDPhaseLogId', "foreign_keys": [], "time": {"start": 'StartTime', "end": 'EndTime'},
                            "attributes": ['CSDPhaseLogId', 'CSDPhaseId', 'StartTime', 'EndTime'],
                            },
            'CSDSeries': {"index": 'CSDSeriesId', "foreign_keys": [],
                          "attributes": ['CSDSeriesId', 'CSDBlockId'],
                          },
            'CSDBlock': {"index": 'CSDBlockId', "foreign_keys": [],
                         "attributes": ['CSDBlockId', 'LiftNumber', 'mCL', 'bCL'],
                         },
            'CSDCorner': {"index": 'CSDCornerId', "foreign_keys": ['CSDPhaseLog', 'CutterRecord'],
                          "attributes": ['CSDCornerId', 'CSDPhaseLogId', 'CutterRecordId', 'CSDSeriesId', 'stepSize'],
                          },
            'CSDSwing': {"index": 'CSDSwingId', "foreign_keys": ['CSDCorner', 'CSDPhaseLog'],
                         "attributes": ['CSDSwingId', 'CSDCornerId', 'CSDPhaseLogId', 'radius', 'centerX', 'centerY']
                         },
            }

# due to foreign key restraints, writes must take place in the order:
# CutterRecord --> CSDPhaseLog --> CSDCorner --> CSDSwing
csd_tables = ["CutterRecord", "CSDPhaseLog", "CSDCorner", "CSDSwing"]

db_to_mdb = {'CutterRecordId': 'index', 'DateTime': 'DateTime', 'CutterX': 'Cutter_X', 'CutterY': 'Cutter_Y', 'TideHeight': 'Tide', 'CenterLineStation': 'Cutter_Sta_on_CL', 'CutterStation': 'Cutter_S', 'CutterRange': 'Cutter_R', 'LadderDepth': 'Ladder_Depth', 'Heading': 'Gyro', 'Velocity': 'Velocity', 'Density': 'Density', 'UnderWaterPumpPower': 'Total_UWP_Kw', 'CutterCurrent': 'Cutter_Mtr_1_Amps', 'CutterSpeed': 'Cutter_Speed', 'PortSwingCurrent': 'Swing_Port_Amps', 'StbdSwingCurrent': 'Swing_Stbd_Amps', 'SuctionPressure': 'Inter_Pressure', 'DischargePressure': 'Disch_Pressure', 'PortPumpSpeed': 'Main_Port_Pump_Rpm', 'StbdPumpSpeed': 'Main_Stbd_Pump_RPM', 'SwingSpeed': 'Swing_Speed', 'InSituDensity': 'Insitu_Density', 'WaterDensity': 'Fluid_Density', 'Booster1Pump1IncomingPressure': 'Booster1_In1_Press', 'Booster1Pump1DischargePressure': 'Booster1_Out1_Press', 'Booster1Pump1Speed': 'Booster1_Pump1_Rpm', 'Booster2Pump1IncomingPressure': 'Booster2_In1_Press', 'Booster2Pump1DischargePressure': 'Booster2_Out1_Press', 'Booster2Pump1Speed': 'Booster2_Pump1_Rpm'}
mdb_to_db = dict([(db_to_mdb[n], n) for n in db_to_mdb.keys()])


def applyCSDPhases(df, CSDPhaseLog_df):
    """This function applies CSDPhaseLogId values to the individual timestamps"""
    print("Applying phase log id's to timestamps...")
    df["CSDPhaseLogId"] = -1
    idx = pd.IndexSlice

    for index, row in CSDPhaseLog_df.iterrows():
        # time.sleep(0.1)
        s_mask_pre = df.loc[:, 'DateTime'] >= row['StartTime']
        s_mask_curr = df.loc[:, 'DateTime'] < row['EndTime']
        s_mask_ch = df.loc[:, 'CSDPhaseLogId'] == -1
        s_mask = np.logical_and(s_mask_pre, s_mask_curr)
        s_mask = np.logical_and(s_mask, s_mask_ch)

        df.loc[idx[s_mask], 'CSDPhaseLogId'] = index
        # df.loc[idx[s_mask], 'Step_Size'] = row['Step_Size']
        # df.loc[idx[s_mask], 'Swing_ID'] = swing_id
        # swing_id += 1


def calc_heading_error(df):
    rel_theta = SwingRadius.calc_new_thetas(df["CutterX"], df["Gps_X"], df["CutterY"], df["Gps_Y"])
    diff = (np.degrees(rel_theta) - (90 - df["Heading"]) + 90) % 360 - 90
    return diff


def buildCSDPhaseLog(df):
    print("Building phase log...")
    df.set_index('index', inplace=True, drop=False)

    table = 'CSDPhaseLog'
    attr = db_schema[table]["attributes"]

    last = df.shape[0] - 1
    back = pd.Series(df.loc[: last - 1, 'CSD_Phase'].values)
    forward = pd.Series(df.loc[1:last, 'CSD_Phase'].values)

    state_change = back.ne(forward)
    mask = [True] + list(state_change.values)
    mask = pd.Series(mask, index=range(0, df.shape[0]))

    idx = pd.IndexSlice
    get_attr = ['CSD_Phase', 'DateTime']
    CSDPhaseLog_df = df.loc[idx[mask], get_attr]

    CSDPhaseLog_df.sort_values('DateTime')
    CSDPhaseLog_df = pd.DataFrame(CSDPhaseLog_df.values, columns=attr[1:-1])

    end_times = list(CSDPhaseLog_df['StartTime'].values)[1:]
    fin_year = str(end_times[-1])[:4]
    fin_month = str(end_times[-1])[5:7]
    fin_day = str(end_times[-1])[8:10]

    fin_stamp = datetime.strptime('%s/%s/%s 23:59:59' % (fin_month, fin_day, fin_year), '%m/%d/%Y %X')
    CSDPhaseLog_df[attr[-1]] = pd.Series(end_times + [fin_stamp])
    CSDPhaseLog_df.index.name = attr[0]

    return CSDPhaseLog_df


# TODO: adjust to grab outer most point
def buildCornerTable(df):
    print("Building corner table...")
    df.set_index('index', inplace=True, drop=False)
    table = 'CSDCorner'
    attr = db_schema[table]["attributes"]
    idx = pd.IndexSlice

    CSDCorner_df = pd.DataFrame()

    for csd_phase in [3, 4]:
        mask_p = df.loc[:, 'CSD_Phase'] == csd_phase
        p_corners = df.loc[idx[mask_p], ['CSDPhaseLogId', 'Gyro', 'CSD_Phase']].copy()
        p_corners.reset_index(inplace=True, drop=False)

        if csd_phase == 3:
            p_corners = p_corners.groupby("CSDPhaseLogId").min()
        else:
            p_corners = p_corners.groupby("CSDPhaseLogId").max()

        p_corners.reset_index(inplace=True, drop=False)

        p_steps = df.loc[idx[mask_p], ['CSDPhaseLogId', 'Step_Size']].groupby("CSDPhaseLogId").sum()
        p_steps = pd.Series(list(p_steps['Step_Size'].values))

        p_corners['stepSize'] = p_steps

        # temp_df = p_corners.loc[:, ['index', ]]
        CSDCorner_df = pd.concat([CSDCorner_df, p_corners])

    to_db = {'index': 'CutterRecordId'}
    CSDCorner_df.drop(['Gyro', 'CSD_Phase'], axis=1, inplace=True)
    CSDCorner_df.sort_values('index', inplace=True)
    rename_trait_cols(CSDCorner_df, to_db, contains_all=False)

    CSDCorner_df.reset_index(inplace=True, drop=True)
    CSDCorner_df.index.name = attr[0]

    return CSDCorner_df


def buildCutterRecord(df):
    print("Building CutterRecord...")
    table = 'CutterRecord'
    attr = db_schema[table]["attributes"]

    # i_back = 8
    # last = df.shape[0] - 1
    # back = pd.Series(list(df.loc[:(last - i_back), 'Cutter_Sta_on_CL'].values))
    # forward = pd.Series(list(df.loc[i_back:last, 'Cutter_Sta_on_CL'].values))
    # delta_CL = list((back - forward).values)
    # df['DeltaCL'] = pd.Series(i_back*[0] + delta_CL, index=range(0, df.shape[0]))


    CutterRecord_df = df.loc[:, list(mdb_to_db.keys())].copy()
    rename_trait_cols(CutterRecord_df, mdb_to_db)
    # CutterRecord_df['Portswing'] = df['Portswing']
    CutterRecord_df['Cutter_SOG'] = df['Cutter_SOG']
    # CutterRecord_df['Corrected_SS'] = df['Corrected_SS']
    CutterRecord_df['DeltaCL'] = df['DeltaCL']
    CutterRecord_df['CSDPhaseLogId'] = df['CSDPhaseLogId']
    CutterRecord_df['Frequency'] = df['Frequency']
    CutterRecord_df['DredgeName'] = df['DredgeName']
    CutterRecord_df['Spud_X'] = df['Spud_X']
    CutterRecord_df['Spud_Y'] = df['Spud_Y']
    CutterRecord_df['Gps_X'] = df['Gps_X']
    CutterRecord_df['Gps_Y'] = df['Gps_Y']
    CutterRecord_df['HeadingError'] = calc_heading_error(CutterRecord_df)


    return CutterRecord_df


def buildSwingTable(df, CSDPhaseLog_df, corner_df):
    df.set_index('index', inplace=True, drop=False)
    table = 'CSDSwing'
    attr = db_schema[table]["attributes"]
    idx = pd.IndexSlice

    # CSDSwing_df = pd.DataFrame()

    mask_ps = CSDPhaseLog_df.loc[:, "CSDPhaseId"] == 1
    mask_ss = CSDPhaseLog_df.loc[:, "CSDPhaseId"] == 2
    s_mask = np.logical_or(mask_ps, mask_ss)

    CSDSwing_df = CSDPhaseLog_df.loc[idx[s_mask], :].copy()
    CSDSwing_df.reset_index(inplace=True, drop=False)
    CSDSwing_df["prevPhaseLogId"] = CSDSwing_df["CSDPhaseLogId"] - 1

    CSDSwing_df["prevPhaseId"] = list(CSDPhaseLog_df.loc[list(CSDSwing_df['prevPhaseLogId'].values), "CSDPhaseId"].values)

    # Port Swings (1) get matched with Stbd corners (4)
    mask_1 = CSDSwing_df.loc[:, "CSDPhaseId"] == 1
    mask_2 = CSDSwing_df.loc[:, "CSDPhaseId"] == 2
    mask_3 = CSDSwing_df.loc[:, "prevPhaseId"] == 3
    mask_4 = CSDSwing_df.loc[:, "prevPhaseId"] == 4
    mask_a1 = np.logical_and(mask_1, mask_4)
    mask_a2 = np.logical_and(mask_2, mask_3)
    f_mask = np.logical_or(mask_a1, mask_a2)

    CSDSwing_df = CSDSwing_df.loc[idx[f_mask], :]
    temp_corner = corner_df.reset_index(inplace=False, drop=False)
    temp_corner = temp_corner.set_index('CSDPhaseLogId', inplace=False, drop=False)

    CSDSwing_df["CSDCornerId"] = list(temp_corner.loc[list(CSDSwing_df['prevPhaseLogId'].values), "CSDCornerId"].values)

    CSDSwing_df.drop(['prevPhaseLogId', 'prevPhaseId', 'CSDPhaseId', "StartTime", "EndTime"], axis=1, inplace=True)
    CSDSwing_df.reset_index(inplace=True, drop=True)
    CSDSwing_df.index.name = attr[0]

    return CSDSwing_df


def add_steps_tp_swing(swing_df, corner_df):
    print("Adding steps to swing...")
    swing_df = swing_df.join(corner_df, on="CSDCornerId", rsuffix="_R")

    swing_df.drop(['CSDPhaseLogId_R', 'CutterRecordId'], axis=1, inplace=True)

    return swing_df


def calc_new_steps(swing_df):
    swing_df.sort_values('CSDSwingId', inplace=True)
    swing_df["stepSizeN"] = -100

    last = swing_df.shape[0] - 1

    delta_x = (swing_df.loc[1:, "CenterX"].values - swing_df.loc[:last - 1, "CenterX"].values) ** 2
    delta_y = (swing_df.loc[1:, "CenterY"].values - swing_df.loc[:last - 1, "CenterY"].values) ** 2
    step = np.sqrt(delta_x + delta_y)
    print(step.shape)

    swing_df.loc[1:, "stepSizeN"] = step


def mainBuildTables(processed_df, swing_radius=False, testing=False):
    new_time = time.time()
    total_time = 0

    print()

    CSDPhaseLog_df = buildCSDPhaseLog(processed_df)

    applyCSDPhases(processed_df, CSDPhaseLog_df)
    CSDCorner = buildCornerTable(processed_df)

    CutterRecord = buildCutterRecord(processed_df)

    CSDSwing = buildSwingTable(processed_df, CSDPhaseLog_df, CSDCorner)

    if swing_radius:
        new_time, total_time = print_time(new_time, total_time, "Time to build tables before swing radii: ", "diff", breaks=False)
        SwingRadius.calc_swing_radius_by_center(CutterRecord, CSDSwing, testing=testing)
        new_time, total_time = print_time(new_time, total_time, "Time to calculate swing radii: ", "diff", breaks=False)
        print(sub_break)

    CSDSwing = add_steps_tp_swing(CSDSwing, CSDCorner)
    # calc_new_steps(CSDSwing)

    freq = processed_df['Frequency'][0]
    dredge_name = processed_df['DredgeName'][0]
    CSDPhaseLog_df['Frequency'] = freq
    CSDPhaseLog_df['DredgeName'] = dredge_name
    CSDCorner['Frequency'] = freq
    CSDCorner['DredgeName'] = dredge_name
    CSDSwing['Frequency'] = freq
    CSDSwing['DredgeName'] = dredge_name

    tables_dict = {
        "CSDCorner": CSDCorner,
        "CSDPhaseLog": CSDPhaseLog_df,
        "CSDSwing": CSDSwing,
        "CutterRecord": CutterRecord,
    }

    return tables_dict




