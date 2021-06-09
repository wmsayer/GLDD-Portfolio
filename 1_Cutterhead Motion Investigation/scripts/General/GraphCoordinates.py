import networkx as nx
import numpy as np
import pandas as pd
from pandas import DataFrame

InFile = 'C:\\Users\\WSayer\\Desktop\\Productions\\Tableau\\Datasource\\HopperData\\References\\GeneralRefDB.csv'
CodeType = 'latin1' # https://docs.python.org/3/library/codecs.html#standard-encodings
Src_Column = 'EstPropNumber'
Tgt_Column = 'RefProject'
CoordsFile = 'C:\\Users\\WSayer\\Desktop\\Productions\\Tableau\\Datasource\\HopperData\\References\\Graph_Coords.csv'
BridgeFile = 'C:\\Users\\WSayer\\Desktop\\Productions\\Tableau\\Datasource\\HopperData\\References\\BridgeFile.csv'

# Read in Source file (add Index Column manually)...
df_InputData = pd.read_csv(InFile,sep=',',encoding=CodeType)
arr_SrcTgt = np.array(df_InputData[[Src_Column,Tgt_Column]])

# Create Network Graph Coordinates...
Q = nx.Graph()
Q.add_edges_from(arr_SrcTgt)
dict_Coords = nx.spring_layout(Q)

# Create Graph Coordinates File...
df_Raw_Coords = DataFrame(dict_Coords)
df_Raw_Coords = df_Raw_Coords.T
df_Raw_Coords.columns = ['X','Y']
df_Raw_Coords.to_csv(CoordsFile,index_label='NodeName')

# Create Bridge File...
# Tableau Code: IF [Src-Tgt]/2 = ROUND([Src-Tgt]/2) THEN 'Source' ELSE 'Target' END
arr_SrcTgt2 = arr_SrcTgt.reshape(1,(len(arr_SrcTgt)*2))
arr_SrcTgt2 = arr_SrcTgt2.reshape(-1)
df_SrcTgt = DataFrame(arr_SrcTgt2,columns=['NodeName'])
arr_Index = []
for i in range(1,(len(arr_SrcTgt)+1)):
    arr_Index.append(i)
    arr_Index.append(i)
df_SrcTgt['c_Index'] = arr_Index
df_SrcTgt.to_csv(BridgeFile,index_label='Src-Tgt')

print('Run Completed Successfully')
