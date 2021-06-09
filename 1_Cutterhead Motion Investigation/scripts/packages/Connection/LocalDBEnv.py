import pandas as pd

# plants_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\Plants.csv"
local_csd_table_root = 'output\\mainStream\\'


db_root_path = "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database"
plants = pd.read_csv(db_root_path + "\\Plants.csv")
dredge_name_dict = dict(zip(list(plants["DredgeInitials"].values), list(plants["DredgeName"].values)))
plant_type_dict = dict(zip(list(plants["DredgeInitials"].values), list(plants["PlantType"].values)))
plant_num_dict = dict(zip(list(plants["DredgeInitials"].values), list(plants["PlantNumber"].values)))
