from packages.CSDPhaseRx import ClassifyPhase
from packages.CSDPhaseRx.BuildCSDTables import mainBuildTables, csd_tables, db_schema
from packages.Connection.LocalDBEnv import *
# from AggregateStats import *
from packages.General.Admin import *
from packages.Connection.Connection import load_classified_csv, combine_data_from_dir, get_full_file_list, combine
import pandas as pd
import numpy as np
import math

idx = pd.IndexSlice
root_table_dir = local_csd_table_root


def combine_master_tables(r_path):
    for table in csd_tables:
        print("\nCombining " + table + ":")
        combined_df = combine_data_from_dir(r_path, f_type=".csv", dir_contains="CHI", file_contains=table)

        if not combined_df.empty:
            combined_df.to_csv(r_path + "\\master\\" + table + ".csv")


def classify_from_raw(dredge_name, raw_df=pd.DataFrame(), f_path=""):
    """Can handle ".csv" with given path or pandas DataFrame"""

    if raw_df.empty:
        if f_path:
            print("Loading raw data from:\n\t%s" % f_path)
            raw_df = pd.read_csv(f_path)
        else:
            print("ERROR: Data not provided.")
            return raw_df

    raw_df = format_datetime(raw_df)
    drop_idx_cols(raw_df)

    processed_df = ClassifyPhase.csd_recognize(raw_df, dredge_name)

    return processed_df


def write_tables(tables_dir, tables_dict, new_write=True, write_CR=False):
    # schema for cache {table: {offset: int, new_start: int}}
    for_key_cache = {}
    table_list = csd_tables.copy()

    if not write_CR:
        table_list.remove('CutterRecord')

    # this function assumes 'csd_tables' is ordered with respect to foreign key restraints
    for table in table_list:
        print("\tWriting table --- %s" % table)
        table_path = tables_dir + '\\' + table + '.csv'
        table_df = tables_dict[table]
        table_df.reset_index(inplace=True, drop=False)

        if new_write:
            write_df = table_df
        else:
            for_key_cache[table] = {"offset": 0, "local_start": 0}

            print("\tReading master table %s" % table)
            master_df = pd.read_csv(table_path)
            master_df = master_df.loc[:master_df.shape[0]-3, :]

            index_col = db_schema[table]["index"]
            offset_i = max(master_df[index_col].values) + 1

            if table == 'CSDPhaseLog':
                last_time = np.max(master_df.loc[:, db_schema[table]["time"]["end"]].values)
                write_mask = table_df[db_schema[table]["time"]["start"]] >= last_time
                # temp_df = table_df.loc[idx[write_mask], index_col]
                for_key_cache[table]["local_start"] = min(table_df.loc[idx[write_mask], index_col].values)
                # offset_i -= for_key_cache[table]["local_start"]

            for_key_cache[table]["offset"] = offset_i

            key_checks = [table] + db_schema[table]["foreign_keys"]
            write_mask = np.array([True]*table_df.shape[0])
            for kt in key_checks:
                k_col = db_schema[kt]["index"]

                if kt in list(for_key_cache.keys()):
                    table_df[k_col] = table_df[k_col] + for_key_cache[kt]["offset"] - for_key_cache[kt]["local_start"]

                    temp_mask = table_df[db_schema[kt]["index"]] >= for_key_cache[kt]["offset"]
                    write_mask = np.logical_and(write_mask, temp_mask)

            for_key_cache[table]["local_start"] += min(table_df.loc[idx[write_mask], index_col].values) - for_key_cache[table]["offset"]

            new_df = table_df.loc[idx[write_mask], :]
            write_df = master_df.append(new_df, ignore_index=True)

        write_df.to_csv(table_path, index=False)


def get_filename(root, f_name="default", subdir="", batch_num=0):
    save_path = root + "\\" + subdir + "\\" + f_name

    if batch_num >= 0:
        save_path += "_Batch-%03d" % batch_num
    save_path += ".csv"

    return save_path


def run_combine(run_name, run_dict, f_list=[], batch_num=0):

    if f_list:
        combined_df = combine(f_list, f_type=run_dict["raw"]["f_type"])
    else:
        combined_df = combine_data_from_dir(run_dict["raw"]["root"],
                                            f_type=run_dict["raw"]["f_type"],
                                            dir_contains=run_dict["raw"]["dir_contains"],
                                            file_contains=run_dict["raw"]["file_contains"])
    drop_idx_cols(combined_df)

    if run_dict["save_combined"]:
        save_path = get_filename(run_dict["raw"]["root"], f_name=run_name, subdir="raw", batch_num=batch_num)
        print("Saving combined data to:\n%s" % save_path)
        combined_df.to_csv(save_path, index=False)
    else:
        print("Combined dataframe not saved")

    return combined_df


def run_basic_classification(run_name, run_dict, raw_df=pd.DataFrame(), batch_num=0):
    read_path = get_filename(run_dict["raw"]["root"], f_name=run_name, subdir="raw", batch_num=batch_num)
    proc_data = classify_from_raw(run_dict["dredge"], raw_df=raw_df, f_path=read_path)

    if run_dict["save_classified"]:
        save_path = get_filename(run_dict["raw"]["root"], f_name=run_name, subdir="classified", batch_num=batch_num)
        print("\nSaving classified data to:\n%s" % save_path)
        proc_data.to_csv(save_path, index=False)
    else:
        print("Classified dataframe not saved")

    return proc_data


def run_csd_tables_batches(run_name, run_dict, swing_radius=False, testing=False, read_batch_num=0, classified_df=pd.DataFrame(), delete_existing=True):
    new_time = time.time()
    total_time = 0

    # table_dir = root_table_dir + run_dict["tables_subdir"] + "\\" + run_name
    table_dir = run_dict["root"] + "\\tables"

    if classified_df.empty:
        print("Loading classified data from disk...")
        read_path = get_filename(run_dict["raw"]["root"], f_name=run_name, subdir="classified", batch_num=read_batch_num)
        classified_df = load_classified_csv(read_path)
        new_time, total_time = print_time(new_time, total_time, "\tTime to load classified data: ", "diff", breaks=False)
    # print("Classified data has shape: %s" % repr(classified_df.shape))

    batch_size = run_dict["batch_size"]
    if batch_size < 1:
        num_batches = 1
        batch_size = classified_df.shape[0]
    else:
        num_batches = math.ceil(classified_df.shape[0] / batch_size)

    print(sub_break + "\nBuilding tables --- Number of Batches: %d --- Batch Size: %d" % (1, batch_size))

    for i in range(0, num_batches):
        print("\t\t----- Write batch %d of %d -----" % (i, num_batches))
        min_i = i * batch_size
        min_i = max(0, min_i)

        max_i = (i + 1) * batch_size
        max_i = min(max_i, classified_df.shape[0]) - 1

        print("\tBatch includes Rows %d to %d of %d" % (min_i, max_i, classified_df.shape[0]-1))
        classified_batch = classified_df.loc[min_i: max_i, :].copy()

        temp_tables_dict = mainBuildTables(classified_batch,
                                           swing_radius=swing_radius,
                                           testing=testing)

        new_time, total_time = print_time(new_time, total_time, "\tTime to build data tables: ", "diff")

        if table_dir:
            print("Saving Tables to -- %s" % table_dir)
            new_write = delete_existing and i == 0 and read_batch_num == 0
            write_tables(table_dir, temp_tables_dict, new_write=new_write, write_CR=run_dict["write_CutterRecord"])
            new_time, total_time = print_time(new_time, total_time, "\tTime to write batch to data tables: ", "diff")
        else:
            print("\tNo table directory provided. Tables not saved/updated.")

    new_time, total_time = print_time(new_time, total_time,
                                      "Total time to write %d batches: " % num_batches, "total", breaks=False)


def run_csd_process(inst_name, inst_dict):
    f_list = get_full_file_list(inst_dict["raw"]["root"], inst_dict["raw"]["f_type"],
                                dir_contains=inst_dict["raw"]["dir_contains"],
                                file_contains=inst_dict["raw"]["file_contains"])
    print(double_break + "\nStarting CSD Processing on --- %s\n" % inst_name + double_break)
    num_files = len(f_list)
    print("Total files to batch through: %d\n%s" % (num_files, repr(f_list)))
    batch_size = inst_dict["raw"]["batch_size"]
    num_batches = math.ceil(num_files/batch_size)
    overlap = 1

    new_time = time.time()
    total_time = 0

    for b in range(0, num_batches):
        print(break_line + "\n" + "Starting Read Batch %d of %d \n" % (b, num_batches) + break_line)
        lower_bi = max(0, b*batch_size - overlap)
        upper_bi = min(num_files, lower_bi + batch_size)
        batch_list = f_list[lower_bi:upper_bi]
        print("Files in Batch %d:\n%s" % (b, repr(batch_list)))

        combined_df = pd.DataFrame()
        if inst_dict["combine"]:
            combined_df = run_combine(inst_name, inst_dict, f_list=batch_list)
        else:
            print("Skipping combine process...")

        classified_df = pd.DataFrame()
        if inst_dict["classify"] or inst_dict["combine"]:
            classified_df = run_basic_classification(inst_name, inst_dict, raw_df=combined_df, batch_num=b)
        else:
            print("Skipping classification process...")

        if inst_dict["build_tables"]:
            run_csd_tables_batches(inst_name, inst_dict, swing_radius=inst_dict["swing_radius"], read_batch_num=b,
                                   classified_df=classified_df, testing=inst_dict["plot_radius_graphs"])
        else:
            print("Skipping table building process...")

    new_time, total_time = print_time(new_time, total_time, "\tTotal time to run %s: " % inst_name, "diff")

    # comb_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\output\\mainStream\\CutterheadInvestigation"
    # combine_master_tables(comb_path)
    # new_time, total_time = print_time(new_time, total_time, "Time to combine tables: ", "diff", breaks=True)


if __name__ == "__main__":
   print("Hi.")
