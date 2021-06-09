from ProdPackages.CSDPhaseRx import mainStream


run_inst = {
    "testIL": ["static\\mainStream\\testData.csv",
               "testIL"],
    "TXCutterHead3":
        ["C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\classified\\TXCombinedData.csv",
        "CutterheadInvestigation\\TX3SecCHI"],
    "ILCutterHead": [
        "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Townsends\\classified\\ILTownsendsCombinedClassified.csv",
        "CutterheadInvestigation\\ILTownsendsCHI"],
    "TXCutterHead1": [
        "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\OneSec\\classified\\TXCombinedData1.csv",
        "CutterheadInvestigation\\TX1SecCHI"],
    "CRCutterHead5": [
        "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Carolina\\classified\\CRChxCombinedClassified.csv",
        "CutterheadInvestigation\\CRChx_5Sec_CHI"],
    "TXCutterHead5": [
        "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Texas5sec\\classified\\TXChxCombinedClassified.csv",
        "CutterheadInvestigation\\TX5SecCHI"],
    "TXGPSCheck": [
        "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\TexasGPSCheck\\classified\\TXGPSCheckClassified.csv",
        "CutterheadInvestigation\\TXGPSCheck"],
    "Ohio_PV": [
        "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\CSD\\raw\\072735 Ponte Vedra\\temp\\OH_PVClassified.csv",
        "72735 Ponte Vedra"],
    # "CR_FullDataset": ["C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Carolina\\FullDataset\\raw\\CR_Classified_FullDataset.csv",
    #                 "CutterheadInvestigation\\CR_FullDataset"],
}

instance_dict = {
    "Ohio_PV": {
        "dredge": "OH",
        "root": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\Database\\CSD\\raw\\072735 Ponte Vedra\\temp",
        "read_ext": "\\OH_PVCombined.csv",
        "write_ext": "\\OH_PVClassified.csv"
    },

    "CR_FullDataset": {
        "dredge": "CR",
        "raw": {
            "root": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Carolina\\FullDataset",
            "f_type": ".mdb",
            "file_contains": "CR",
            "dir_contains": "",
            "batch_size": 0,
            },
        "save_combined": False,
        "save_classified": True,
        "tables_subdir": "CutterheadInvestigation",
        "combine": False,
        "classify": False,
        "build_tables": True,
        "swing_radius": True,
        "plot_radius_graphs": False,
        "delete_existing_tables": True,
        "batch_size": 0,
    },

    "CR_BatchFullDataset": {
        "dredge": "CR",
        "root": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Carolina\\FullDataset",
        "raw": {
            "root": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\Carolina\\FullDataset",
            "f_type": ".mdb",
            "file_contains": "CR",
            "dir_contains": "",
            "batch_size": 10,
        },
        "save_combined": False,
        "save_classified": True,
        "tables_subdir": "CutterheadInvestigation",
        "combine": True,
        "classify": True,
        "build_tables": True,
        "swing_radius": True,
        "plot_radius_graphs": False,
        "delete_existing_tables": True,
        "batch_size": 0,
        "write_CutterRecord": False,
    },

    "TX_BatchFullDataset": {
        "dredge": "TX",
        "root": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\TX_BatchFullDataset",
        "raw": {
            "root": "C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation\\TX_BatchFullDataset",
            "f_type": ".mdb",
            "file_contains": "TX",
            "dir_contains": "",
            "batch_size": 10,
        },
        "save_combined": False,
        "save_classified": True,
        "tables_subdir": "CutterheadInvestigation",
        "combine": True,
        "classify": True,
        "build_tables": True,
        "swing_radius": True,
        "plot_radius_graphs": False,
        "delete_existing_tables": True,
        "batch_size": 0,
        "write_CutterRecord": False,
    },
}

run_inst_name = "TX_BatchFullDataset"
instance_dict["inst_name"] = run_inst_name
# mainStream.run_csd_process(run_inst_name, instance_dict[run_inst_name])

mainStream.combine_master_tables("C:\\Users\\WSayer\\PycharmProjects\\CSDPhaseRecognition\\CSDPhaseRx\\static\\CSDCutterheadInvestigation")