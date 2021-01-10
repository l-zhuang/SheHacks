import numpy as np
import pandas as pd
#import os

data=pd.read_csv(r"C:\Users\lzhua\OneDrive\Desktop\MedMo\myapp\DataSet\nutrients_csvfile.csv")
data_found=data.loc[data.Food=='Custard']
value=int((data_found['Carbs']).iloc[0])
#v=int(value.)
#vI=int(v)
print(value)


eValue=5
#fV=v/g*eValue


#print(fV)
#print(carb['Calories'][0])