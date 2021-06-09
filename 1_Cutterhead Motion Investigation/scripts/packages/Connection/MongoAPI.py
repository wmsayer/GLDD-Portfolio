from pymongo import MongoClient
# pprint library is used to make the output look more pretty
from pprint import pprint

# connect to MongoDB, change the << MONGODB URL >> to reflect your own connection string
client = MongoClient("mongodb://192.168.18.223:27017/HopperData.Terrapin Island")
db = client.admin
# Issue the serverStatus command and print the results
serverStatusResult=db.command("serverStatus")
pprint(serverStatusResult)

from packages.Connection.Connection import *
from packages.General.Admin import *

db_root_path = "..\\Database"
plants = pd.read_csv(db_root_path + "\\Plants.csv")
hopper_dbi, db_types = load_tshd_db_index()


def main_hopper_db():
    root_path = "C:\\Users\\WSayer\\Desktop\\terra"
    # db_path =

    for dredge in ["Dodge", "Ellis", "Liberty", "Padre", "Terrapin"]:
        print("\nCombining %s Island..." % dredge)

        temp_path = root_path + "\\" + dredge + " Island"
        to_ext = dredge + "_Island_Master.csv"

        for db_type in ["Dig", "Pump", "Sail"]:
            df = combine_data_from_dir(temp_path, f_type=".csv", dir_contains="*",
                                       file_contains=db_type, header=13)
            df.to_csv(root_path + "\\" + to_ext)


def basic_concat_hopper_db():
    root_path = "C:\\Users\\WSayer\\Desktop\\terra"
    dredge = "Terrapin Island"

    idx = pd.IndexSlice
    plant_num = plants.loc[idx[plants["DredgeName"] == dredge, "PlantNumber"]].values[0]

    for db_type in ["Sail"]:
        df = combine_data_from_dir(root_path, f_type=".csv", dir_contains="*", file_contains=db_type)

        df["hopperId"] = plant_num

        if "Dredge" in df.columns:
            df.drop(columns=["Dredge"], inplace=True)

        rename_trait_cols(df, hopper_dbi[db_type]["col_dict"], contains_all=False)

        new_db = insert_data(hopper_dbi[db_type], df)

        to_ext = dredge + "_Master.csv"
        df.to_csv(root_path + "\\" + to_ext, index=False)

        new_db.to_csv(hopper_dbi[db_type]["path"], index=False)


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


def check_mdb_cols():
    root_path = "C:\\Users\\WSayer\\Desktop\\Data Innovation\\Sample Datasets"
    db_type = "mdb"

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
        temp = load_full_csd_mdb(file[1]).fillna(0) != 0
        check = temp.any(axis=0)
        check_df = pd.DataFrame(check.values.reshape(1, -1), index=[file[0]], columns=check.index)

        final_df = pd.concat([final_df, check_df], axis=0, ignore_index=False)

    final_df = final_df.fillna(-99)
    final_df = final_df.applymap(lambda x: 1 if x == True else x)
    final_df = final_df.applymap(lambda x: 0 if x == False else x)
    print(final_df)

    final_df.to_csv(root_path + "\\" + db_type + "_cols.csv")


if __name__ == "__main__":
    main_comment_parse()

