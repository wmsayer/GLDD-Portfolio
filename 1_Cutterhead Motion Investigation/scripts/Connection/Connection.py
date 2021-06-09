from packages.General.Admin import format_datetime, drop_idx_cols
import pandas as pd
import pathlib
import glob
from datetime import datetime
import pyodbc


def query_mdb(f_name, query):
    """This function loads a full day's .mdb data. In order to connect to .mbd with the following method your
    Python bit size must match your Microsoft Office bit size 32-bit Microsoft Office requires 32-bit Python
    or else you will get an error."""

    # path must be the machine-specific path

    if f_name[0:2] != "C:":
        # path = "%s" % pathlib.Path(__file__).parent.absolute() + "\static\%s" % f_name
        path = "%s" % pathlib.Path(__file__).parent.parent.absolute() + f_name
    else:
        path = f_name

    print(path)

    cnxn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=%s;' % path)

    cnxn = pyodbc.connect(cnxn_str)
    cnxn.autocommit = True

    try:
        dataf = pd.read_sql(query, cnxn)
    except:
        dataf = pd.DataFrame()
        print("Error, could not read file: \n%s" % path)

    cnxn.close()

    return dataf


def load_full_csd_mdb(f_name, format_dt=True):
    query = "SELECT * FROM Hydro"
    csd_df = query_mdb(f_name, query)

    # concatenate datetime
    if not csd_df.empty and format_dt:
        csd_df = format_datetime(csd_df)

    return csd_df


def update_file_dir(file, new_name, f_ext=".csv", sep="\\"):
    file_dir = file.split(sep)
    file_dir[-1] = new_name + f_ext
    new_file = sep.join(file_dir)
    return new_file


def query_azure_sql(db_dict, query_str):
    # query = build_insert_query(query_dict["table"], query_dict["query_dict"])
    server = 'dredge-sensor-test.database.windows.net'
    database = 'CSDSensor'
    username = 'ToastyAlmond'
    password = '{grb;23TlRack}'
    # driver = '{ODBC Driver 173 for SQL Server}'
    driver = '{SQL Server}'
    # cxn_str = "Driver=%s;Server=tcp:%s,1433;Database=%s;Uid=%s;Pwd=%s;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;" % \
    #           (driver, server, database, username, password)

    cnx_str = 'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password
    print(cnx_str)

    # cxn_str = r"DRIVER={ODBC Driver 13 for SQL Server};" \
    #           r"SERVER=tcp:dredge-sensor-test.database.windows.net,1433;" \
    #           r"DATABASE=CSDSensor;" \
    #           r"UID=ToastyAlmond;" \
    #           r"PWD={grb;23TlRack}"

    with pyodbc.connect(cnx_str) as conn:
    # with pyodbc.connect(cxn_str) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_str)
            # row = cursor.fetchone()
            # while row:
            #     print(str(row[0]) + " " + str(row[1]))
            #     row = cursor.fetchone()


def get_dir_names(root_dir, f_ext="", contains="", narrate=True):

    if contains == "*":
        contains = ""

    if narrate:
        print('Looking in:\n%s' % root_dir)
        print('\nExtension:\n%s' % f_ext)
        print('\nContains:\n%s' % contains)
        print('\nFiles within criteria are:')

    file_list = []

    for file in glob.glob("%s\\*%s" % (root_dir, f_ext)):
        if file.find(contains) > -1:
            file_list += [file]

            if narrate:
                print(file)

    if narrate:
        print('\nTotal files found: %d' % len(file_list))

    return file_list


def combine(file_list, f_type="", header='infer'):
    master = pd.DataFrame()

    for fn in file_list:
        temp = pd.DataFrame()

        if f_type == ".csv" or f_type == ".drg" or f_type == ".pro":
            print(fn)
            try:
                temp = pd.read_csv(fn, header=header, skipinitialspace=True)
            except:
                print("Header position incorrect or file empty!!")
                temp = pd.DataFrame()

        if f_type == ".mdb":
            temp = load_full_csd_mdb(fn)

        # if temp.columns in master.columns:
        master = pd.concat([master, temp])
        # else:
        #     print("Columns don't match!!")

    return master


def combine_data_from_dir(root_path, f_type, dir_contains="", file_contains="", narrate=False, header='infer'):
    file_list = get_full_file_list(root_path, f_type, dir_contains=dir_contains, file_contains=file_contains,
                                   narrate=narrate)

    master_df = combine(file_list, f_type, header=header)

    return master_df


def get_full_file_list(root_path, f_type, dir_contains="", file_contains="", narrate=False):
    """
    This function takes a path and combines all .mdb files into a single .csv.
    It assumes each .mdb file is located in its own daily folder and all daily folders are in the given directory.
    """

    if dir_contains:
        folder_list = get_dir_names(root_path, f_ext="", contains=dir_contains, narrate=narrate)
    else:
        folder_list = [root_path]

    file_list = []

    for fold in folder_list:
        file_list += get_dir_names(fold, f_ext=f_type, contains=file_contains, narrate=narrate)

    return file_list


def load_test_mdb():
    test_pass_times = {'T': [
        (datetime.strptime('11/04/2019 04:57:00', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 09:33:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 14:43:00', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 19:46:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 01:24:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 07:36:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 13:13:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 14:41:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 14:41:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 16:29:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 16:29:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 20:13:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/06/2019 04:16:00', '%m/%d/%Y %X'),
         datetime.strptime('11/06/2019 07:27:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/06/2019 14:50:00', '%m/%d/%Y %X'),
         datetime.strptime('11/06/2019 18:35:00', '%m/%d/%Y %X'))],
        'B': [
            (datetime.strptime('11/04/2019 00:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/04/2019 04:25:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/04/2019 09:44:00', '%m/%d/%Y %X'),
             datetime.strptime('11/04/2019 14:42:59', '%m/%d/%Y %X')),
            (datetime.strptime('11/04/2019 20:06:00', '%m/%d/%Y %X'),
             datetime.strptime('11/04/2019 23:59:59', '%m/%d/%Y %X')),
            (datetime.strptime('11/05/2019 00:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/05/2019 01:24:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/05/2019 07:46:00', '%m/%d/%Y %X'),
             datetime.strptime('11/05/2019 12:45:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/05/2019 20:18:00', '%m/%d/%Y %X'),
             datetime.strptime('11/05/2019 23:59:59', '%m/%d/%Y %X')),
            (datetime.strptime('11/06/2019 00:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/06/2019 04:16:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/06/2019 12:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/06/2019 14:24:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/06/2019 18:42:00', '%m/%d/%Y %X'),
             datetime.strptime('11/06/2019 23:59:59', '%m/%d/%Y %X'))]}

    test_delay_times = [
        (datetime.strptime('11/04/2019 04:25:59', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 04:37:38', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 04:40:52', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 04:51:02', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 04:53:04', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 04:58:40', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 13:12:50', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 13:31:47', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 13:37:36', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 13:48:43', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 19:47:23', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 19:55:30', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 09:27:25', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 09:38:35', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 20:02:46', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 20:06:55', '%m/%d/%Y %X'))]

    f_name = '\\CSDPhaseRx\\static\\IL20191104v.mdb'
    print('Reading file: %s' % f_name)
    dataf = load_full_csd_mdb(f_name)
    dredge = f_name[:2]
    print('Loading %s data from .mdb' % dredge)

    return dataf, dredge, test_delay_times


def load_classified_csv(f_path):
    processed_df = pd.read_csv(f_path)

    # check_cols = ['index', 'level_0', 'Unnamed: 0']
    #
    # for col in check_cols:
    #     if col in processed_df.columns:
    #         processed_df.drop(col, axis=1, inplace=True)

    drop_idx_cols(processed_df)

    processed_df = format_datetime(processed_df)
    return processed_df


def load_all_test_mdbs():
    test_pass_times = {'T': [
        (datetime.strptime('11/04/2019 04:57:00', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 09:33:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 14:43:00', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 19:46:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 01:24:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 07:36:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 13:13:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 14:41:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 14:41:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 16:29:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/05/2019 16:29:00', '%m/%d/%Y %X'),
         datetime.strptime('11/05/2019 20:13:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/06/2019 04:16:00', '%m/%d/%Y %X'),
         datetime.strptime('11/06/2019 07:27:00', '%m/%d/%Y %X')),
        (datetime.strptime('11/06/2019 14:50:00', '%m/%d/%Y %X'),
         datetime.strptime('11/06/2019 18:35:00', '%m/%d/%Y %X'))],
        'B': [
            (datetime.strptime('11/04/2019 00:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/04/2019 04:25:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/04/2019 09:44:00', '%m/%d/%Y %X'),
             datetime.strptime('11/04/2019 14:42:59', '%m/%d/%Y %X')),
            (datetime.strptime('11/04/2019 20:06:00', '%m/%d/%Y %X'),
             datetime.strptime('11/04/2019 23:59:59', '%m/%d/%Y %X')),
            (datetime.strptime('11/05/2019 00:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/05/2019 01:24:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/05/2019 07:46:00', '%m/%d/%Y %X'),
             datetime.strptime('11/05/2019 12:45:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/05/2019 20:18:00', '%m/%d/%Y %X'),
             datetime.strptime('11/05/2019 23:59:59', '%m/%d/%Y %X')),
            (datetime.strptime('11/06/2019 00:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/06/2019 04:16:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/06/2019 12:00:00', '%m/%d/%Y %X'),
             datetime.strptime('11/06/2019 14:24:00', '%m/%d/%Y %X')),
            (datetime.strptime('11/06/2019 18:42:00', '%m/%d/%Y %X'),
             datetime.strptime('11/06/2019 23:59:59', '%m/%d/%Y %X'))]}

    test_delay_times = [
        (datetime.strptime('11/04/2019 04:25:59', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 04:37:38', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 04:40:52', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 04:51:02', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 04:53:04', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 04:58:40', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 13:12:50', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 13:31:47', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 13:37:36', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 13:48:43', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 19:47:23', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 19:55:30', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 09:27:25', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 09:38:35', '%m/%d/%Y %X')),
        (datetime.strptime('11/04/2019 20:02:46', '%m/%d/%Y %X'),
         datetime.strptime('11/04/2019 20:06:55', '%m/%d/%Y %X'))]

    f_name = '\\CSDPhaseRx\\static\\IL20191104v.mdb'
    print('Reading file: %s' % f_name)
    dataf = load_full_csd_mdb(f_name)

    return dataf, test_delay_times


# TODO: implement SQL from PostDredge db whenever available
def connect_sqlite():
    return


def load_tshd_db_index(db_root="..\\Database\\TSHD"):
    hopper_db = {}
    # db_types = ["Dig", "Pump", "Sail"]
    db_types = ["Sail"]

    for db_type in db_types:
        hopper_db[db_type] = {"path": db_root + "\\Hopper%s.csv" % db_type,
                              "index": "hopper%sId" % db_type,
                              "alt_index": ["projectNumber", "hopperId", "loadNumber"],
                              "col_path": db_root + "\\columns\\%sColumns.csv" % db_type}

        cols = pd.read_csv(hopper_db[db_type]["col_path"])
        col_dict = dict(zip(list(cols["PD_Output_Name"].values), list(cols["DB_Name"].values)))
        hopper_db[db_type]["col_dict"] = col_dict

    return hopper_db, db_types


if __name__ == "__main__":
    print("\nSee \"Tests.py\" for tests.")

