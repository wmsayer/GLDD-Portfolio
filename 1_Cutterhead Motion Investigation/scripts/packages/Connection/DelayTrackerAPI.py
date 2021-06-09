from packages.General.Admin import *
from packages.Connection.Connection import query_mdb
import packages.Connection.LocalDBEnv as dbenv

idx = pd.IndexSlice


def test_from_DT_online():
    plants_df = dbenv.plants
    plants_dict = dict(zip(plants_df["DredgeName"], plants_df["DredgeInitials"]))

    local_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\DelayTracker\\DelayTrackerDB_70000.csv"
    print("\nReading Delay Tracker Local DB:\n%s\n" % local_path)
    delay_tracker_df = pd.read_csv(local_path)

    dt_format = '%m/%d/%Y %X'
    delay_tracker_df["StartDate"] = pd.to_datetime(delay_tracker_df["StartDate"].values, format=dt_format)
    delay_tracker_df["FinishDate"] = pd.to_datetime(delay_tracker_df["FinishDate"].values, format=dt_format)
    delay_tracker_df["DurationMinutes"] = delay_tracker_df["FinishDate"] - delay_tracker_df["StartDate"]
    delay_tracker_df["DurationMinutes"] = delay_tracker_df["DurationMinutes"].dt.total_seconds()/60

    delay_tracker_df["DredgeInitials"] = delay_tracker_df["VesselName"]
    delay_tracker_df["DredgeInitials"] = delay_tracker_df["DredgeInitials"].map(plants_dict)
    # delay_tracker_df.replace({"DredgeInitials": plants_dict}, inplace=True)

    to_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\DelayTracker\\DelayTrackerDB_70000_post.csv"
    delay_tracker_df.to_csv(to_path, index=False)


def test_read_local_dtdb():
    root_path = "C:\\Users\\WSayer\\Desktop\\Productions\\Job Tracking\\72761 Jupiter Island\\ProjectDB\\DelayTrackerDB"
    read_path = root_path + "\\DelayTracker"
    write_path = root_path + "\\DelayTracker.csv"

    delay_df = load_delay_tracker_mdb(read_path)
    delay_df.to_csv(write_path, index=False)


def load_delay_tracker_mdb(f_name):
    query = "SELECT *, HopperCycles.StartDate AS LoadStart, HopperCycles.FinishDate AS LoadEnd \n" \
               "FROM (StatesLog\n" \
               "LEFT JOIN HopperStates ON StatesLog.HopperState = HopperStates.HopperStateID)\n" \
               "LEFT JOIN HopperCycles ON StatesLog.HopperCycle = HopperCycles.HopperCycleID\n"

    print(query)
    dt_df = query_mdb(f_name, query)

    return dt_df


if __name__ == "__main__":
    test_read_local_dtdb()
