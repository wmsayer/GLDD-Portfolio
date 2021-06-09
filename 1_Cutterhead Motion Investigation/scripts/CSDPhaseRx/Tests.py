from packages.CSDPhaseRx import ClassifyPhase, ClassifyPhaseKMeans
from packages.General import Admin
from packages.Connection import Connection
from packages.Connection.SQLapi.SQLAdmin import build_insert_query
from Project.PredictiveMaintenance import clean_liberty
import numpy as np
import pandas as pd
import math


def test_determine_swing_dir():
    # initialize test datasets as full port and stbd swings that cross direct North
    port1 = np.linspace(30, 1, 30)
    port2 = np.linspace(359, 330, 30)
    test_port = np.concatenate((port1, port2))
    test_stbd = np.flip(test_port)
    test_port_df = pd.DataFrame(test_port, columns=['Gyro'])
    test_stbd_df = pd.DataFrame(test_stbd, columns=['Gyro'])

    # test port swing
    port_test_df = ClassifyPhase.determine_swing_dir(test_port_df, 5)
    print(port_test_df)
    port_test_result = port_test_df.loc[:, 'Portswing'].all()

    # test stbd swing
    stbd_test_df = ClassifyPhase.determine_swing_dir(test_stbd_df, 5)
    print(stbd_test_df)
    stbd_test_result = not stbd_test_df.loc[:, 'Portswing'].any()

    # display results
    result = {True: "Pass", False: "Fail"}
    print("Port Swing Test: " + result[port_test_result])
    print("Stbd Swing Test: " + result[stbd_test_result])

    return [port_test_result, stbd_test_result]


def test_csd_recognize():
    dataf, test_delay_times = Connection.load_test_mdb()
    # proc_data = RecognizePhaseStream.csd_recognize(dataf, delay_times=test_delay_times)
    proc_data = ClassifyPhase.csd_recognize(dataf, "IL")
    proc_data.to_csv('static\\mainStream\\testDataDelay.csv')


def test_kmeans():
    dataf, dredge, test_delay_times = Connection.load_test_mdb()
    # dataf = Connection.load_classified_csv("C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\static\\72663 Dredge Data\\UnzippedMDB\\output\\ILcombinedCSDData.csv")
    proc_data = ClassifyPhase.csd_recognize(dataf.copy(), dredge)

    proc_data_km, feats, default = ClassifyPhaseKMeans.prepare_features(dataf, dredge)
    ClassifyPhaseKMeans.run_kmeans(proc_data_km, feats, default)

    proc_data_km["CSDPhaseId"] = proc_data["CSD_Phase"]
    proc_data_km.to_csv('static\\mainStream\\testDataKMeans.csv')


def test_combine_mdb_from_dir():
    # r_path = "C:\\Users\\WSayer\\Desktop\\72663 Dredge Data\\UnzippedMDB"

    # r_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\static\\CSDCutterheadInvestigation\\Townsends"
    # to_file = "\\ILTownsendsCombined.csv"

    # r_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\static\\CSDCutterheadInvestigation\\Carolina"
    # to_file = "\\CRChxCombined.csv"

    r_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\CSD\\raw\\072735 Ponte Vedra"
    to_file = "\\temp\\OH_PVCombined.csv"

    combined_df = Connection.combine_data_from_dir(r_path, f_type=".mdb", dir_contains="", file_contains="OH2020111")
    combined_df.to_csv(r_path + to_file, index=False)


def test_combine_pro_from_dir():
    r_path = "C:\\Users\WSayer\\Desktop\\Data Innovation\\Predictive Maintenance\\Sample Datasets\\Liberty\\PRO_Liberty"
    to_file = "\\LI_Combined.csv"

    combined_df = Connection.combine_data_from_dir(r_path, f_type=".pro", dir_contains="", file_contains="LB")
    combined_df.to_csv(r_path + to_file, index=False)


def test_azure():
    test_db = Connection.load_full_csd_mdb("C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\CSD\\raw\\072735 Ponte Vedra\\OH20201030.mdb", format_dt=False)
    # test_db.drop(['Field1'], inplace=True, axis=1)
    n = 900
    for i in range(0, math.ceil(test_db.shape[0]/n)):
        min_i = i*n
        max_i = (i+1)*n
        max_i = min(max_i, test_db.shape[0]) - 1

        query_dict = {"table": "OhioSensor", "columns": test_db.columns, "records": test_db.loc[min_i: max_i, :].to_dict('records')}
        query_str = build_insert_query(query_dict, type="records")
        print("Inserting Row %d to %d of %d" % (min_i, max_i, test_db.shape[0]))
        # print(query_str)
        Connection.query_azure_sql({}, query_str)


def test_combine_csv():
    root_path = "C:\\Users\\WSayer\\Desktop\\Productions\\Job Tracking\\72761 Jupiter Island\\ProjectDB\\PLCData"
    read_path = root_path + "\\Daily"
    write_path = root_path + "\\PLCDataMaster.csv"
    f_type = ".csv"
    df = Connection.combine_data_from_dir(read_path, f_type, dir_contains="", file_contains="", narrate=False, header='infer')
    print(df)
    Admin.format_datetime(df)

    df = clean_liberty(df)
    df.to_csv(write_path, index=False)


if __name__ == "__main__":
    test_combine_csv()
