import pandas as pd
df=pd.read_excel("roads_assam_synthetic_v2.xlsx")
print("TOTAL ROADS:",len(df))
print("HIGH RISK:",(df.risk_level=="HIGH").sum())
print("MEDIUM RISK:",(df.risk_level=="MEDIUM").sum())
print("LOW RISK:",(df.risk_level=="LOW").sum())
print("\nALTERNATE ROUTE SCENARIOS:")
for pair,g in df.groupby(["origin_district","destination_district"]):
    if len(g)>1: print(pair, "->", g.road_id.astype(str).tolist())
print("\nNO-ALTERNATE SCENARIOS:")
for pair,g in df.groupby(["origin_district","destination_district"]):
    if len(g)==1: print(g.road_id.iloc[0], "->", pair)
