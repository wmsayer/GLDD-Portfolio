# Cutterhead Motion Investigation

The purpose of this study was to show a statistical representation of cutterhead motion for a Cutter Suction Dredge (CSD) during operation. This was executed using

* Python (NumPy, Pandas, matplotlib)
* Tableau

## Phase 1

This phase served as a **Proof of Concept** of the data processing, modeling, and analytics methods used for the study, as we previously did not have any methods in place to retrieve this sort of data. The methods used to measure motion were dependent on my previous work in `scripts/CSDPhaseRx` which classifies data timestamps into a certain production phase (see README in that sub directory for more details). This classification step is critical in being able to measure cutterhead motion.

With it being only PoC, Phase 1 was performed on a smaller dataset consisting of ~3 days worth of data from 3 different dredges.

Another purpose of this study was to determine if the **data logging frequency** had a significant effect on the results of the motion calculation. Data was recorded 24/7 at 1, 3, and 5-second intervals and the results were compared.

## Phase 2

This phase served two purposes:

1)	scale the methods and processes from Phase 1 to be performed on a larger dataset
2)	incorporate wave buoy data from a third source to measure the affect of the wave action on cutterhead motion

## Addendum - CSD Model Insights

This addendum was intended to be viewed more as a PowerPoint to help

* visualize the dredge data and underpinning methods behind the `CSDPhaseRx` classification process
* provide insights regarding data quality (e.g. latency, miscalibration) and anamoly detection in sensor readings/calibrations
* provide insights on the performance of the `CSDPhaseRx` model and its ability to classify work time vs delay time (measured against manually input data)
