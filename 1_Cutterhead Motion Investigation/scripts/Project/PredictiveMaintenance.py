from packages.Connection.Connection import *
from packages.Connection.PROCnnx import *
from packages.General.Admin import *
from packages.TSHDStateRx.ClassifyState import tshd_recognize
import packages.Connection.LocalDBEnv as dbenv
from itertools import dropwhile
import csv

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////
# These functions are used to build and clean a dataset that was then sent to a third-party contractor
# that ran the data through their processes in our Predictive Maintenance Pilot
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////


idx = pd.IndexSlice
hopper_dbi, tshd_db_types = load_tshd_db_index()
pm_root = "C:\\Users\\WSayer\\Desktop\\Data Innovation\\Predictive Maintenance\\Datasets"


def basic_concat_hopper_db(root_path = "C:\\Users\\WSayer\\Desktop\\Productions\\Job Tracking\\72761 Jupiter Island\\ProjectDB\\HopperData"):
    read_path = root_path + "\\By Load"

    for db_type in tshd_db_types:
        df = combine_data_from_dir(read_path, f_type=".csv", dir_contains="*", file_contains=db_type)
        dredge_name = df.loc[0, "Dredge"]
        plant_num = dbenv.plants.loc[idx[dbenv.plants["DredgeName"] == dredge_name, "PlantNumber"]].values[0]
        df["PlantNumber"] = plant_num

        if "Dredge" in df.columns:
            df.drop(columns=["Dredge"], inplace=True)

        rename_trait_cols(df, hopper_dbi[db_type]["col_dict"], contains_all=False)

        write_ext = "Hopper" + db_type + "_Master.csv"
        df.to_csv(root_path + "\\" + write_ext, index=False)

        # new_db = insert_data(hopper_dbi[db_type], df)
        # new_db.to_csv(hopper_dbi[db_type]["path"], index=False)


def insert_data(dbi, new_data):
    dbi_col = dbi["index"]
    indices = dbi["alt_index"]
    db = pd.read_csv(dbi["path"])

    db["loadNumber"] = db["loadNumber"].values.astype(int)

    if indices:
        db.set_index(indices, inplace=True, drop=False)
        new_data.set_index(indices, inplace=True, drop=False)

    for i, row in new_data.iterrows():
        if db.index.contains(i):
            print("Value already exists: %s" % repr(i))
            continue
        else:
            print("Inserting value: %s" % repr(i))
            row[dbi_col] = np.max(db[dbi_col].values) + 1
            db = db.append(row)

    # db.set_index(dbi_col, inplace=True, drop=False)

    return db


def check_pro_cols():
    root_path = "C:\\Users\\WSayer\\Desktop\\Data Innovation\\Sample Datasets"
    db_type = "PRO"

    file_list = get_dir_names(root_path + "\\" + db_type, contains="", narrate=False)
    file_info = []
    dredges = []
    ellis_info = []

    for file in file_list:
        dredge = file.split("\\")[-1].split(".")[0]

        if dredge[0:2] == "EI":
            ellis_info.append((dredge, file))

        else:
            file_info.append((dredge, file))
            dredges.append(dredge)

    final_df = pd.DataFrame()

    for file in file_info:
        temp = pd.read_csv(file[1], header=1).fillna(0) != 0
        check = temp.any(axis=0)
        check_df = pd.DataFrame(check.values.reshape(1, -1), index=[file[0]], columns=check.index)

        final_df = pd.concat([final_df, check_df], axis=0, ignore_index=False)

    final_df = final_df.fillna(-99)
    final_df = final_df.applymap(lambda x: 1 if x == True else x)
    final_df = final_df.applymap(lambda x: 0 if x == False else x)
    print(final_df)

    final_df.to_csv(root_path + "\\" + db_type + "_cols.csv")



def pred_maint_clean_dataset(dredge_init, col_rev="R0", tz_shift=0, clean_data=False):
    dredge_name = dbenv.dredge_name_dict[dredge_init]
    plant_type = dbenv.plant_type_dict[dredge_init]
    f_ext = {"CSD": "mdb", "TSHD": "pro"}[plant_type]

    working_path = pm_root + "\\" + dredge_name
    read_ext = "\\raw"
    write_ext = "\\reduced"
    feat_ext = "\\GLDD_PM_Cols_" + dredge_init + "_" + col_rev + ".csv"

    file_list = get_dir_names(working_path + read_ext, f_ext=f_ext)

    features = []
    if col_rev:
        features = list(pd.read_csv(working_path + feat_ext)["Datafield"].values)

    dt_col = find_dt_col(features)
    print("Datetime column: %s" % dt_col)
    print("Features: %s" % features)

    for file in file_list:
        file_name = get_filename(file)
        write_path = working_path + write_ext + "\\" + file_name + ".csv"

        process_fn = {"mdb": load_full_csd_mdb,
                      "csv": read_csv,
                      "pro": clean_read_pro
                      }
        raw_df = process_fn[f_ext](file)

        if raw_df.empty:
            continue

        if tz_shift != 0:
            # print(raw_df[dt_col])
            raw_df[dt_col] = raw_df[dt_col] + pd.to_timedelta("%dhr" % tz_shift)
            print(raw_df[dt_col])

        if clean_data and dredge_init == "LI":
            tshd_recognize(raw_df, dredge_init)

        if features:
            red_df = raw_df.loc[:, features]
        else:
            red_df = raw_df

        red_df.to_csv(write_path, index=False)


if __name__ == "__main__":
    run_dredge = "LI"
    col_rev = "R2"
    pred_maint_clean_dataset(run_dredge, col_rev=col_rev, tz_shift=5, clean_data=True)



