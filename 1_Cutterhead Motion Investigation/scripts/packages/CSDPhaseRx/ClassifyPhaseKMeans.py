from packages.General.Admin import *
from packages.General.FeatureCleaning import *

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score


def basic_classifications(df, cols, default):
    idx = pd.IndexSlice
    df["SwingDirection"] = default
    df["FutureDirection"] = default
    df["SwingDirection45"] = default
    df["FutureDirection45"] = default

    mask1 = df.loc[:, cols] != default
    mask1 = mask1.all(axis=1)

    # -1 indicates PORT and 1 indicates STBD
    weight = 2
    df.loc[idx[mask1], "SwingDirection"] = weight*np.where(df.loc[idx[mask1], "RG_B20"].values > 0, 1, -1)
    df.loc[idx[mask1], "FutureDirection"] = weight*np.where(df.loc[idx[mask1], "RG_F45"].values > 0, -1, 1)

    df.loc[idx[mask1], "Cutter_SOG"] = df.loc[idx[mask1], "Cutter_SOG"].values / np.mean(df.loc[idx[mask1], "Cutter_SOG"].values)
    df.loc[idx[mask1], "Spud_SOG"] = df.loc[idx[mask1], "Spud_SOG"].values / np.mean(df.loc[idx[mask1], "Spud_SOG"].values)
    df.loc[idx[mask1], "MA_Density"] = (df.loc[idx[mask1], "MA_Density"].values - 1)*5
    df.loc[idx[mask1], "MA_Velocity"] = (df.loc[idx[mask1], "MA_Velocity"].values / np.mean(df.loc[idx[mask1], "MA_Velocity"].values))*1.5
    df.loc[idx[mask1], "Gyro_Rate"] = np.abs(df.loc[idx[mask1], "Gyro_Rate"].values * 4)


def run_kmeans(df, final_features, default=-99):
    print(df.shape)
    idx = pd.IndexSlice
    # mask1 = df.loc[:, final_features] != default
    # pd.set_option("display.max_rows", 20, "display.max_columns", 20)
    # mask1 = mask1.all(axis=1)
    # X = df.loc[idx[mask1], final_features]

    X, mask = remove_def_tups(df, final_features, default)
    X.loc[:, :] = (X.values - np.mean(X.values, axis=0)) / np.std(X.values, axis=0)

    print(X.shape)
    print(X)

    k_list = list(range(2, 11))
    k_inertias = []
    k_labels = []
    k_centers = []
    k_scores = []
    model_list = []

    for k in k_list:
        print("Running KMeans for %d clusters..." % k)
        col_name = "Labels_KM_%d" % k
        model = MiniBatchKMeans(n_clusters=k, batch_size=256, random_state=12345).fit(X)
        model_list.append(model)
        cluster_assignments = model.labels_
        score = silhouette_score(X, cluster_assignments, metric='euclidean')
        inertia = model.inertia_
        k_scores.append(score)
        k_inertias.append(inertia)
        k_labels.append(model.labels_)
        k_centers.append(model.cluster_centers_)
        df[col_name] = -1
        df.loc[idx[mask], col_name] = model.labels_

    plt.figure(figsize=(8, 4), dpi=120)
    plt.title('The Elbow Plot')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Sum of Square Distances')
    _ = plt.plot(k_list, k_inertias, 'bo--')
    plt.show()


    # 3D Plot
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(xs=X["Relative_Gyro_B_20"].values, ys=X["Relative_Gyro_F_45"].values, zs=X["Rate_Gyro_B_5"].values, cmap=cm.coolwarm)
    #
    # plt.show()


if __name__ == "__main__":
    data_paths = {
        "Ohio": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\CSD\\raw\\072735 Ponte Vedra\\OH_PVCombined.csv",
        "Liberty Island": "C:\\Users\\WSayer\\Desktop\\Data Innovation\\Predictive Maintenance\\Sample Datasets\\Liberty\\PRO_Liberty\\LI_Combined.csv"
    }

    to_paths = {
        "Ohio": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\CSD\\raw\\072735 Ponte Vedra\\OH_PV_Reduced.csv",
        "Liberty Island": "C:\\Users\\WSayer\\Desktop\\Data Innovation\\Predictive Maintenance\\Sample Datasets\\Liberty\\PRO_Liberty\\LI_Reduced.csv"
    }

    columns = "C:\\Users\\WSayer\\Desktop\\Data Innovation\\Predictive Maintenance\\Sample Datasets\\PredictiveMaintenancePLCDatafields.csv"

    dredge = "Ohio"
    default_val = -99

    calc_dicts = {"Ohio": {
                    # 'Cutter_SOG': {"type": "SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default,
                    #                "columns": {"X": "Cutter_X", "Y": "Cutter_Y", "DateTime": "DateTime"}},
                    'Spud_SOG': {"type": "SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
                                   "columns": {"X": "Spud_X", "Y": "Spud_Y", "DateTime": "DateTime"}},
                    'GPS_SOG': {"type": "SOG", "time": 5, "time_unit": "min", "direction": "backward", "default": default_val,
                                 "columns": {"X": "Gps_X", "Y": "Gps_Y", "DateTime": "DateTime"}},
                    'RG_B20': {"type": "Relative", "time": 20, "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro"},
                    # 'RG_F20': {"type": "Relative", "time": 20, "frequency": time_int, "direction": "forward", "default": default, "column": "Gyro"},
                    # 'RG_B45': {"type": "Relative", "time": 45, "frequency": time_int, "direction": "backward", "default": default, "column": "Gyro"},
                    'RG_F45': {"type": "Relative", "time": 45, "frequency": 5, "direction": "forward", "default": default_val, "column": "Gyro"},
                    # 'RG_B60': {"type": "Relative", "time": 60, "frequency": time_int, "direction": "backward", "default": default, "column": "Gyro"},
                    # 'RG_F60': {"type": "Relative", "time": 60, "frequency": time_int, "direction": "forward", "default": default, "column": "Gyro"},
                    # 'MA_Density': {"type": "MovAvg", "time": 15, "frequency": time_int, "direction": "center", "default": default, "column": "Density"},
                    # 'MA_Velocity': {"type": "MovAvg", "time": 15, "frequency": time_int, "direction": "center", "default": default, "column": "Velocity"},
                    'Gyro_Rate': {"type": "Rate", "time": 5, "time_unit": "sec", "frequency": 5, "direction": "backward", "default": default_val, "column": "Gyro", "abs": True},
                    },
                }

    raw_df = pd.read_csv(data_paths[dredge])
    cols = pd.read_csv(columns)

    print(raw_df.columns)
    fin_cols = list(cols[dredge].dropna().values)

    if dredge == "Ohio":
        # classified_df = load_classified_csv(run_path[curr_run][0])
        dataf, new_feats = prepare_features(format_datetime(raw_df.loc[:500000, :]), calc_dicts[dredge], "OH")
        dataf, mask = remove_def_tups(dataf, new_feats, default_val)
        fin_cols += new_feats
    else:
        dataf = format_datetime(raw_df)
        dataf[' Port Density'] = np.where(dataf[' Port Density'].values < 1, 1, dataf[' Port Density'].values)
        dataf[' Stbd Density'] = np.where(dataf[' Stbd Density'].values < 1, 1, dataf[' Stbd Density'].values)

        dataf[' Port Velocity [fps]'] = np.where(dataf[' Port Velocity [fps]'].values < 0, 0,
                                                 dataf[' Port Velocity [fps]'].values)
        dataf[' Stbd Velocity [fps]'] = np.where(dataf[' Stbd Velocity [fps]'].values < 0, 0,
                                                 dataf[' Stbd Velocity [fps]'].values)

    print(fin_cols)

    red_df = dataf.loc[:, fin_cols]
    red_df.to_csv(to_paths[dredge], index=False)



