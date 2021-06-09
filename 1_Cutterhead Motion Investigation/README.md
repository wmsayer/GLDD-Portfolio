# Cutterhead Motion Investigation

The purpose of this study was to show a statistical representation of cutterhead motion for a Cutter Suction Dredge (CSD) during operation. This was executed using Python (NumPy, Pandas, matplotlib) and Tableau.

## Phase 1

This phase served as a Proof of Concept more the data processing, modeling, and analytics methods used for the study as we previously had none. These processes were dependent on my previous work in `scripts/CSDPhaseRx` which classifies data timestamps into a certain production phase. This classification step is critical in being able to measure cutterhead motion.

With it being only PoC this phase was performed on a smaller dataset consisting of ~3 days of data from 3 different dredges.

Another purpose of this study was to determine if data logging frequency had a significant effect on the results of the motion calculation. Data was recorded 24/7 at 1, 3, and 5-second intervals and the results were compared.

## Phase 2

This phase served two purposes:

	1)	scale the methods and processes from Phase 1 to be performed on a larger dataset
	2)	incorporate wave buoy data from a third source to measure the affect of the wave action on cutterhead motion


