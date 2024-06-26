# -*- coding: utf-8 -*-
"""CyanoProject_1_DataCleaning

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1MGBgBO6NqXYJgn8VrCxskbQpgCCJfnMS
"""

## Read in csvs
import pandas as pd

# google trends data (Ohio, LA, SF, Sac)
ohio_google = pd.read_csv("Ohio_wholestate.csv", skiprows=2) #we have extra info in first 2 rows, so skipping those
caLA_google = pd.read_csv("California_LosAngeles.csv", skiprows=2)
caSF_google = pd.read_csv("California_SanFrancisco.csv", skiprows=2)
caSac_google = pd.read_csv("California_Sacramento.csv", skiprows=2)
cawholestate_google = pd.read_csv("California_wholestate.csv", skiprows = 2)

# Lake Erie microcystins
df = pd.read_csv('mcyst.csv', encoding='latin1')

# California bloom report
bloom_reports = pd.read_csv("bloom-report.csv")

## Cleaning Lake Erie microcystins data
import numpy as np

df.replace({'Particulate Microcystin (µg/L)': {'<0.1': 0, np.nan: 0},
            'Dissolved Microcystin (µg/L)': {'<0.1': 0, np.nan: 0}}, inplace=True)
#print(df)

# Step 1: Change date format to mm/yyyy and fill missing months
df['Particulate Microcystin (µg/L)'] = pd.to_numeric(df['Particulate Microcystin (µg/L)'], errors='coerce')
df['Dissolved Microcystin (µg/L)'] = pd.to_numeric(df['Dissolved Microcystin (µg/L)'], errors='coerce')


df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date').resample('M').sum()
df = df.reset_index()
df['Date'] = df['Date'].dt.strftime('%m/%Y')

#print(df)

# Step 4: Create a new column representing YYYYMM
df['YYYYMM'] = pd.to_datetime(df['Date'], format='%m/%Y').dt.strftime('%Y%m')

# Step 5: Sort the DataFrame by 'YYYYMM' in ascending order
df = df.sort_values(by='YYYYMM')

# Step 6: Drop the temporary 'YYYYMM' column
df.drop(columns=['YYYYMM'], inplace=True)
#print(df.head())

## Cleaning California bloom report data for whole state (1/2)

#print(bloom_reports)
#print(bloom_reports.shape[0]) #2841 total

## (1) removing columns we don't care about

# columns we care about
columns = ["Bloom_Date_Created", "Water_Body_Name", "Regional_Water_Board", "Reported_Advisory_Types", "Water_Body_Type",
           "Advisory_Recommended"]
bloom_reports_cleaning = bloom_reports.filter(items = columns)

## (2) dealing w/ missing data and making labeling consistent

# seeing if there is any missing data
print(bloom_reports_cleaning.isnull().sum())
# we will decided how to deal with this later but Reported_Adivsory_Type is missing a huge chunk of data
# we may decide to use "Advisory_Recommended" instead

# but for now, let's remove the 143 rows that are missing dates
bloom_reports_cleaning.dropna(subset=['Bloom_Date_Created'], inplace=True)
#print(bloom_reports_cleaning.shape[0]) # now 2698 total

# and for those missing "Water_Body_Type", let's see if we can infer that information from the water body name
#print(bloom_reports_cleaning["Water_Body_Type"].unique())
# we have reservoir, wadeable stream, nonwadeable stream, pond, wetland, stormwater retention, and lake
# combine nonwadeable and wadeable stream to "rivers & streams" and make reservoirs and ponds as "Lake"
# and put stormwater retention into other
bloom_reports_cleaning = bloom_reports_cleaning.replace(to_replace= "Wadeable stream",  value="Rivers & streams")
bloom_reports_cleaning = bloom_reports_cleaning.replace(to_replace= "Nonwadeable stream",  value="Rivers & streams")
bloom_reports_cleaning = bloom_reports_cleaning.replace(to_replace= "Reservoir",  value="Lake")
bloom_reports_cleaning = bloom_reports_cleaning.replace(to_replace= "Pond (<1 ha)",  value="Lake")
bloom_reports_cleaning = bloom_reports_cleaning.replace(to_replace= "Stormwater retention",  value="Other")
bloom_reports_cleaning = bloom_reports_cleaning.replace(to_replace= "Wetland",  value="Other")

# seeing what water_body_names exist
#print(bloom_reports_cleaning["Water_Body_Name"].unique())

# making function to assign water body type
# making new column for marine as there are shorelines, estuaries and lagoons!
def assign_water_body_type(name):
  if "lake" in name.lower():
    return "Lake"
  elif "reservoir" in name.lower():
    return "Lake"
  elif "pond" in name.lower():
    return "Lake"
  elif "river" in name.lower():
    return("Rivers & streams")
  elif "stream" in name.lower():
    return("Rivers & streams")
  elif "creek" in name.lower():
    return("Rivers & streams")
  elif "bay" in name.lower():
    return("Marine")
  elif "estuary" in name.lower():
    return("Marine")
  elif "beach" in name.lower():
    return("Marine")
  elif "sea" in name.lower():
    return("Marine")
  else:
    return("Other")

# make a new column for above function
bloom_reports_cleaning["Derived_Water_Body_Type"] = bloom_reports_cleaning["Water_Body_Name"].apply(assign_water_body_type)

# if we are missing information from the original water_body_type column, use the derived type to fill that in
# otherwise keep original information inputted by the state official
def adjust_water_body(row):
  if pd.isnull(row["Water_Body_Type"]):
    return row["Derived_Water_Body_Type"]
  else:
    return row["Water_Body_Type"]

# apply function across rows
bloom_reports_cleaning["Final_Water_Body_Type"] = bloom_reports_cleaning.apply(adjust_water_body, axis = 1)
#print(bloom_reports_cleaning["Final_Water_Body_Type"].unique())

# dealing with advisory level posted or recommended (we want to be "None", "Caution", "Warning", or "Danger")
#print(bloom_reports_cleaning["Reported_Advisory_Types"].unique())
#print(bloom_reports_cleaning["Advisory_Recommended"].unique())
# we will work with "Reported_Advisory_Types" because in this case we know communication actually happened
# a "general awareness sign" probably means there was no public health issues regarding the bloom
# as a "caution" level or higher requires a caution sign

# assigning report level with above criteria in mind
def assign_report_level(name):
  test = str(name) # column not processing as a string
  if "caution" in test.lower():
    return "Caution"
  elif "danger" in test.lower():
    return "Danger"
  elif "warning" in test.lower():
    return "Warning"
  elif "none" in test.lower():
    return "None"
  elif "alert sign" in test.lower():
    return "Caution"
  elif "general awareness" in test.lower():
    return "None"
  elif "NA - refer to Report Details" in test.lower():
    return "Unknown"
  else:
    return "Unknown"

# apply function
bloom_reports_cleaning["Adjusted_Reported_Advisory"] = bloom_reports_cleaning["Reported_Advisory_Types"].apply(assign_report_level)
#print(bloom_reports_cleaning["Adjusted_Reported_Advisory"].unique()) # we now have 5 categories- 4 report levels and unknown

## (3) aggregate by month and year and calculate number of reports per month

# making everything the appropriate data type (string) instead of an object
bloom_reports_cleaning = bloom_reports_cleaning.convert_dtypes()

# need to make the date column a datetime object rather than a string
bloom_reports_cleaning["Bloom_Date_Created"] = pd.to_datetime(bloom_reports_cleaning["Bloom_Date_Created"])

# get month and year from datetime object
bloom_reports_cleaning["Year"] = bloom_reports_cleaning["Bloom_Date_Created"].dt.year
bloom_reports_cleaning["Month"] = bloom_reports_cleaning["Bloom_Date_Created"].dt.month

# now, can aggregate by location -> year -> and then month
aggregate = bloom_reports_cleaning.groupby(['Year', 'Month']).size()
bloom_reports_aggregated = aggregate.reset_index()
bloom_reports_aggregated.rename(columns={0: "Total_Num_Reports"}, inplace = True) # rename column
#print(bloom_reports_aggregated.head())
#print(bloom_reports_aggregated.shape[0]) # this compacts our dataframe down to 94 rows

# now, aggregate by waterbody type -> location -> year -> and then month
aggregate_waterbody = bloom_reports_cleaning.groupby(["Final_Water_Body_Type", 'Year', 'Month']).size()
bloom_reports_aggregated_waterbody = aggregate_waterbody.reset_index()
bloom_reports_aggregated_waterbody.rename(columns={0: "Num_Reports_WB"}, inplace = True) # rename column
#print(bloom_reports_aggregated_waterbody.head())

# creating mini dataframes for each category (there is probably a better way to do this...)
lake_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Lake"]
lake_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Lake"}, inplace = True)
lake_counts = lake_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(lake_counts.head())
river_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Rivers & streams"]
river_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Rivers"}, inplace = True)
river_counts = river_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(river_counts.head())
marine_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Marine"]
marine_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Marine"}, inplace = True)
marine_counts = marine_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(marine_counts.head())
other_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Other"]
other_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Other"}, inplace = True)
other_counts = other_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(other_counts.head())

# merge into bloom_reports_aggregated total based on metro, year, month
final_ws = pd.merge(bloom_reports_aggregated, lake_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = 'left')
final_ws = pd.merge(final_ws, river_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = 'left')
final_ws = pd.merge(final_ws, marine_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = 'left')
final_ws = pd.merge(final_ws, other_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = 'left')
final_ws = final_ws.fillna(0) # fill in missing values as 0
#print(final_ws.head()) # looks good!
#print(final_ws.shape[0]) # still the same size (94) so everything is good!

# now, lastly by advisory type -> location -> year -> and then month
aggregated_advisory = bloom_reports_cleaning.groupby(["Adjusted_Reported_Advisory", 'Year', 'Month']).size()
bloom_reports_aggregated_advisory= aggregated_advisory.reset_index()
bloom_reports_aggregated_advisory.rename(columns={0: "Num_Reports_Advisory"}, inplace = True) # rename column
#print(bloom_reports_aggregated_advisory.head())

# creating mini dataframes for each category (there is probably a better way to do this...)
noadvisory_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "None"]
noadvisory_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_NoAdvisory"}, inplace = True)
noadvisory_counts = noadvisory_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(noadvisory_counts.head())
caution_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Caution"]
caution_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_Caution"}, inplace = True)
caution_counts = caution_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(caution_counts.head())
warning_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Warning"]
warning_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_Warning"}, inplace = True)
warning_counts = warning_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(warning_counts.head())
danger_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Danger"]
danger_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_Danger"}, inplace = True)
danger_counts = danger_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(danger_counts.head())
unknown_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Unknown"]
unknown_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_UnknownAdvisory"}, inplace = True)
unknown_counts = unknown_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(unknown_counts.head())

# merge into bloom_reports_aggregated total based on metro, year, month
final_ws = pd.merge(final_ws, noadvisory_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = "left")
final_ws = pd.merge(final_ws, caution_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = "left")
final_ws = pd.merge(final_ws, warning_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = "left")
final_ws = pd.merge(final_ws, danger_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = "left")
final_ws = pd.merge(final_ws, unknown_counts, left_on=["Year", "Month"], right_on=["Year", "Month"], how = "left")
final_ws = final_ws.fillna(0) # fill in missing values as 0
#print(final_ws.tail()) # looks good!
#print(final_ws.shape[0]) # still the same size (94) so everything is good!

## (5) calculate percentages of each category

# simple pandas math!
final_ws["Percent_Lake"] = (final_ws["Num_Reports_Lake"] / final_ws["Total_Num_Reports"])
final_ws["Percent_River"] = (final_ws["Num_Reports_Rivers"] / final_ws["Total_Num_Reports"])
final_ws["Percent_Marine"] = (final_ws["Num_Reports_Marine"] / final_ws["Total_Num_Reports"])
final_ws["Percent_Other"] = (final_ws["Num_Reports_Other"] / final_ws["Total_Num_Reports"])
final_ws["Percent_NoAdvisory"] = (final_ws["Num_Reports_NoAdvisory"] / final_ws["Total_Num_Reports"])
final_ws["Percent_Caution"] = (final_ws["Num_Reports_Caution"] / final_ws["Total_Num_Reports"])
final_ws["Percent_Warning"] = (final_ws["Num_Reports_Warning"] / final_ws["Total_Num_Reports"])
final_ws["Percent_Danger"] = (final_ws["Num_Reports_Danger"] / final_ws["Total_Num_Reports"])
final_ws["Percent_UnknownAdvisory"] = (final_ws["Num_Reports_UnknownAdvisory"] / final_ws["Total_Num_Reports"])
#print(final_ws.head())

## Cleaning California bloom report dataset for 3 metros (2/2)

## (1) filtering out for metros we care about

# rows we care about
locations = ["Region 2 - San Francisco Bay", "Region 4 - Los Angeles", "Region 5 - Central Valley", "Region 8 - Santa Ana"]
bloom_reports_cleaning = bloom_reports_cleaning[(bloom_reports_cleaning.Regional_Water_Board == locations[0]) |
                                                (bloom_reports_cleaning.Regional_Water_Board == locations[1]) |
                                                (bloom_reports_cleaning.Regional_Water_Board == locations[2]) |
                                                (bloom_reports_cleaning.Regional_Water_Board == locations[3])]

## (2) ID appropriate regions with matching Google Trends metros
# Region 2 = "SF", Region 4 & 8 = "LA", Region 5 = "Sac"

# making a function to assign metro
def assign_metro(region):
  if region == locations[0]:
    return "SF"
  elif region == locations[2]:
    return "Sac"
  else:
    return "LA"

# assigning metro to "Google_Metro" column
bloom_reports_cleaning['Google_Metro'] = bloom_reports_cleaning['Regional_Water_Board'].apply(assign_metro)

## (3) aggregate by metro and then by month number of reports per month

# making everything the appropriate data type (string) instead of an object
bloom_reports_cleaning = bloom_reports_cleaning.convert_dtypes()

# need to make the date column a datetime object rather than a string
bloom_reports_cleaning["Bloom_Date_Created"] = pd.to_datetime(bloom_reports_cleaning["Bloom_Date_Created"])

# get month and year from datetime object
bloom_reports_cleaning["Year"] = bloom_reports_cleaning["Bloom_Date_Created"].dt.year
bloom_reports_cleaning["Month"] = bloom_reports_cleaning["Bloom_Date_Created"].dt.month

# now, can aggregate by location -> year -> and then month
aggregate = bloom_reports_cleaning.groupby(['Google_Metro', 'Year', 'Month']).size()
bloom_reports_aggregated = aggregate.reset_index()
bloom_reports_aggregated.rename(columns={0: "Total_Num_Reports"}, inplace = True) # rename column
#print(bloom_reports_aggregated.head())
#print(bloom_reports_aggregated.shape[0]) # this compacts our dataframe down to 200 rows

# now, aggregate by waterbody type -> location -> year -> and then month
aggregate_waterbody = bloom_reports_cleaning.groupby(["Final_Water_Body_Type", 'Google_Metro', 'Year', 'Month']).size()
bloom_reports_aggregated_waterbody = aggregate_waterbody.reset_index()
bloom_reports_aggregated_waterbody.rename(columns={0: "Num_Reports_WB"}, inplace = True) # rename column
#print(bloom_reports_aggregated_waterbody.head())

# creating mini dataframes for each category (there is probably a better way to do this...)
lake_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Lake"]
lake_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Lake"}, inplace = True)
lake_counts = lake_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(lake_counts.head())
river_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Rivers & streams"]
river_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Rivers"}, inplace = True)
river_counts = river_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(river_counts.head())
marine_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Marine"]
marine_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Marine"}, inplace = True)
marine_counts = marine_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(marine_counts.head())
other_counts = bloom_reports_aggregated_waterbody.loc[bloom_reports_aggregated_waterbody["Final_Water_Body_Type"] == "Other"]
other_counts.rename(columns={"Num_Reports_WB": "Num_Reports_Other"}, inplace = True)
other_counts = other_counts.drop(labels = "Final_Water_Body_Type", axis = 1)
#print(other_counts.head())

# merge into bloom_reports_aggregated total based on metro, year, month
final_metros = pd.merge(bloom_reports_aggregated, lake_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = 'left')
final_metros = pd.merge(final_metros, river_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = 'left')
final_metros = pd.merge(final_metros, marine_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = 'left')
final_metros = pd.merge(final_metros, wetland_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = 'left')
final_metros = pd.merge(final_metros, other_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = 'left')
final_metros = final_metros.fillna(0) # fill in missing values as 0
#print(final_metros.head()) # looks good!
#print(final_metros.shape[0]) # still the same size (200) so everything is good!

# now, lastly by advisory type -> location -> year -> and then month
aggregated_advisory = bloom_reports_cleaning.groupby(["Adjusted_Reported_Advisory", 'Google_Metro', 'Year', 'Month']).size()
bloom_reports_aggregated_advisory= aggregated_advisory.reset_index()
bloom_reports_aggregated_advisory.rename(columns={0: "Num_Reports_Advisory"}, inplace = True) # rename column
#print(bloom_reports_aggregated_advisory.head())

# creating mini dataframes for each category (there is probably a better way to do this...)
noadvisory_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "None"]
noadvisory_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_NoAdvisory"}, inplace = True)
noadvisory_counts = noadvisory_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(noadvisory_counts.head())
caution_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Caution"]
caution_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_Caution"}, inplace = True)
caution_counts = caution_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(caution_counts.head())
warning_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Warning"]
warning_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_Warning"}, inplace = True)
warning_counts = warning_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(warning_counts.head())
danger_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Danger"]
danger_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_Danger"}, inplace = True)
danger_counts = danger_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(danger_counts.head())
unknown_counts = bloom_reports_aggregated_advisory.loc[bloom_reports_aggregated_advisory["Adjusted_Reported_Advisory"] == "Unknown"]
unknown_counts.rename(columns={"Num_Reports_Advisory": "Num_Reports_UnknownAdvisory"}, inplace = True)
unknown_counts = unknown_counts.drop(labels = "Adjusted_Reported_Advisory", axis = 1)
#print(unknown_counts.head())

# merge into bloom_reports_aggregated total based on metro, year, month
final_metros = pd.merge(final_metros, noadvisory_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = "left")
final_metros = pd.merge(final_metros, caution_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = "left")
final_metros = pd.merge(final_metros, warning_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = "left")
final_metros = pd.merge(final_metros, danger_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = "left")
final_metros = pd.merge(final_metros, unknown_counts, left_on=["Google_Metro", "Year", "Month"], right_on=["Google_Metro", "Year", "Month"], how = "left")
final_metros = final_metros.fillna(0) # fill in missing values as 0
#print(final_metros.tail()) # looks good!
#print(final_metros.shape[0]) # still the same size (200) so everything is good!

## (5) calculate percentages of each category

# simple pandas math!
final_metros["Percent_Lake"] = (final_metros["Num_Reports_Lake"] / final_metros["Total_Num_Reports"])
final_metros["Percent_River"] = (final_metros["Num_Reports_Rivers"] / final_metros["Total_Num_Reports"])
final_metros["Percent_Marine"] = (final_metros["Num_Reports_Marine"] / final_metros["Total_Num_Reports"])
final_metros["Percent_Other"] = (final_metros["Num_Reports_Other"] / final_metros["Total_Num_Reports"])
final_metros["Percent_NoAdvisory"] = (final_metros["Num_Reports_NoAdvisory"] / final_metros["Total_Num_Reports"])
final_metros["Percent_Caution"] = (final_metros["Num_Reports_Caution"] / final_metros["Total_Num_Reports"])
final_metros["Percent_Warning"] = (final_metros["Num_Reports_Warning"] / final_metros["Total_Num_Reports"])
final_metros["Percent_Danger"] = (final_metros["Num_Reports_Danger"] / final_metros["Total_Num_Reports"])
final_metros["Percent_UnknownAdvisory"] = (final_metros["Num_Reports_UnknownAdvisory"] / final_metros["Total_Num_Reports"])
#print(final.head())

## Merging datasets
## Match by date (year/month)
## Merge by column

## Ohio Google trends with microcystins

#rename "Month column to Date"
ohio_google.rename(columns = {'Month': 'Date'}, inplace=True)

#changing Month column to mm/yyyy
ohio_google['Date'] = pd.to_datetime(ohio_google['Date'])
ohio_google['Date'] = ohio_google['Date'].dt.strftime('%m/%Y')
#print(ohio_google)

#join google trend data with Ohio microcystin data using a left join on Date column
mergedOhio = pd.merge(df, ohio_google, how ='left', on ='Date')
#print(mergedOhio)
mergedOhio.to_csv('OhioFinalData.csv', index=False)

## California metro Google trends with report data
# one for SF, one for LA, one for Sacramento
# one for whole state

# #SF DATASET
#First, let's change the month column to a datetime datatype
caSF_google['Month'] = pd.to_datetime(caSF_google['Month'])

#We need to pull apart the month and the year into separate columns to match Jordan's data
caSF_google['Year'] = caSF_google['Month'].dt.year
caSF_google['Month'] = caSF_google['Month'].dt.month

#Let's reorganize the order of the columns to it's year, month, blue green algae
desired_order = ['Year', 'Month', 'blue green algae: (San Francisco-Oakland-San Jose CA)']

# Reassign the DataFrame with the desired column order
caSF_google = caSF_google[desired_order]

#looks good, now let's add a metro column so we can merge this to Jordan's dataset on the metro column
caSF_google['Google_Metro'] = 'SF'

#let's also rename our blue green algae column
caSF_google.rename(columns={'blue green algae: (San Francisco-Oakland-San Jose CA)': 'blue green algae'}, inplace=True)

#Let's go ahead and do the same thing for the LA dataset
# we need to merge on year, then month, then county
#First, let's change the month column to a datetime datatype
caLA_google['Month'] = pd.to_datetime(caLA_google['Month'])

#We need to pull apart the month and the year into separate columns to match Jordan's data
caLA_google['Year'] = caLA_google['Month'].dt.year
caLA_google['Month'] = caLA_google['Month'].dt.month

#Let's reorganize the order of the columns to it's year, month, blue green algae
desired_order = ['Year', 'Month', 'blue green algae: (Los Angeles CA)']

# Reassign the DataFrame with the desired column order
caLA_google = caLA_google[desired_order]

#looks good, now let's add a metro column so we can merge this to Jordan's dataset on the metro column
caLA_google['Google_Metro'] = 'LA'

#let's also rename our blue green algae column
caLA_google.rename(columns={'blue green algae: (Los Angeles CA)': 'blue green algae'}, inplace=True)

# Let's do the same thing for Sac
# we need to merge on year, then month, then county
#First, let's change the month column to a datetime datatype
caSac_google['Month'] = pd.to_datetime(caSac_google['Month'])

#We need to pull apart the month and the year into separate columns to match Jordan's data
caSac_google['Year'] = caSac_google['Month'].dt.year
caSac_google['Month'] = caSac_google['Month'].dt.month

#Let's reorganize the order of the columns to it's year, month, blue green algae
desired_order = ['Year', 'Month', 'blue green algae: (Sacramento-Stockton-Modesto CA)']

# Reassign the DataFrame with the desired column order
caSac_google = caSac_google[desired_order]

#looks good, now let's add a metro column so we can merge this to Jordan's dataset on the metro column
caSac_google['Google_Metro'] = 'Sac'

#let's also rename our blue green algae column
caSac_google.rename(columns={'blue green algae: (Sacramento-Stockton-Modesto CA)': 'blue green algae'}, inplace=True)

#now, let's merge the data
#first we will concat all of the metro data into one df to make it easier to merge to Jordan's data
mergedMetros = pd.concat([caSac_google, caSF_google], axis=0)
mergedMetros = pd.concat([mergedMetros, caLA_google], axis=0)

#now let's merge that into the CA df
mergedCA_metros = pd.merge(final_metros, mergedMetros, on=['Google_Metro', 'Year', 'Month'], how='left')

#write out that data into a csv for download
mergedCA_metros.to_csv('CAFinalData_Metros.csv', index=False)

# #WHOLE STATE DATASET

#First, let's change the month column to a datetime datatype
cawholestate_google['Month'] = pd.to_datetime(cawholestate_google['Month'])

#We need to pull apart the month and the year into separate columns to match Jordan's data
cawholestate_google['Year'] = cawholestate_google['Month'].dt.year
cawholestate_google['Month'] = cawholestate_google['Month'].dt.month

#Let's reorganize the order of the columns to it's year, month, blue green algae
desired_order = ['Year', 'Month', 'blue green algae: (California)']

# Reassign the DataFrame with the desired column order
cawholestate_google = cawholestate_google[desired_order]

#let's also rename our blue green algae column
cawholestate_google.rename(columns={'blue green algae: (California)': 'blue green algae'}, inplace=True)

# Merge whole state datasets
mergedCA_wholestate = pd.merge(final_ws, cawholestate_google, on=['Year', 'Month'], how='left')

#write out that data into a csv for download
mergedCA_wholestate.to_csv('CAFinalData_WholeState.csv', index=False)

# #WHOLE STATE DATASET

#First, let's change the month column to a datetime datatype
cawholestate_google['Month'] = pd.to_datetime(cawholestate_google['Month'])

#We need to pull apart the month and the year into separate columns to match Jordan's data
cawholestate_google['Year'] = cawholestate_google['Month'].dt.year
cawholestate_google['Month'] = cawholestate_google['Month'].dt.month

#Let's reorganize the order of the columns to it's year, month, blue green algae
desired_order = ['Year', 'Month', 'blue green algae: (California)']

# Reassign the DataFrame with the desired column order
cawholestate_google = cawholestate_google[desired_order]

#let's also rename our blue green algae column
cawholestate_google.rename(columns={'blue green algae: (California)': 'blue green algae'}, inplace=True)

# Merge whole state datasets
mergedCA_wholestate = pd.merge(final_ws, cawholestate_google, on=['Year', 'Month'], how='left')

#write out that data into a csv for download
mergedCA_wholestate.to_csv('CAFinalData_WholeState.csv', index=False)