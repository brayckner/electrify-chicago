import pandas
from utils import get_and_clean_csv

data_directory = './source/'
building_emissions_file = 'ChicagoEnergyBenchmarking.csv'
data_out_file = "ChicagoEnergyBenchmarkingAllNewestInstances.csv"

# Columns that should be strings because they are immutable identifiers
string_cols = [
    'ChicagoEnergyRating',
    'ZIPCode'
]

# Int columns that are numbers (and can get averaged) but should be rounded
int_cols = [
    'NumberOfBuildings',
    'ENERGYSTARScore',
    # TODO: Move to string after figuring out why the X.0 is showing up
    'Wards',
    'CensusTracts',
    # 'ZIPCode',
    'CommunityAreas',
    'HistoricalWards2003-2015'
]

if __name__ == "__main__":
    building_data = get_and_clean_csv(data_directory + building_emissions_file)
    replace_headers = {"Data Year": "DataYear",
        "ID": "ID",
        "Property Name": "PropertyName",
        "Reporting Status": "ReportingStatus",
        "Address": "Address",
        "ZIP Code": "ZIPCode",
        "Chicago Energy Rating": "ChicagoEnergyRating",
        "Exempt From Chicago Energy Rating": "ExemptFromChicagoEnergyRating",
        "Community Area": "CommunityArea",
        "Primary Property Type": "PrimaryPropertyType",
        "Gross Floor Area - Buildings (sq ft)": "GrossFloorArea",
        "Total GHG Emissions (Metric Tons CO2e)": "TotalGHGEmissions",
        "GHG Intensity (kg CO2e/sq ft)": "GHGIntensity",
        "Year Built": "YearBuilt",
        "# of Buildings": "NumberOfBuildings",
        "Water Use (kGal)": "WaterUse",
        "ENERGY STAR Score": "ENERGYSTARScore",
        "Electricity Use (kBtu)": "ElectricityUse",
        "Natural Gas Use (kBtu)": "NaturalGasUse",
        "District Steam Use (kBtu)": "DistrictSteamUse",
        "District Chilled Water Use (kBtu)": "DistrictChilledWaterUse",
        "All Other Fuel Use (kBtu)": "AllOtherFuelUse",
        "Site EUI (kBtu/sq ft)": "SiteEUI",
        "Source EUI (kBtu/sq ft)": "SourceEUI",
        "Weather Normalized Site EUI (kBtu/sq ft)": "WeatherNormalizedSiteEUI",
        "Weather Normalized Source EUI (kBtu/sq ft)": "WeatherNormalizedSourceEUI",
        "Latitude": "Latitude",
        "Longitude": "Longitude",
        "Location": "Location",
        "Row_ID": "Row_ID",
        "Wards": "Wards",
        "Community Areas": "CommunityAreas",
        "Zip Codes": "ZipCodes",
        "Census Tracts": "CensusTracts",
        "Historical Wards 2003-2015": "HistoricalWards2003-2015" }
    building_data.rename(columns=replace_headers,inplace=True)

    has_ghg_intensity = building_data.loc[(building_data['GHGIntensity'] > 0)].copy()

    all_submitted_data = has_ghg_intensity.loc[(has_ghg_intensity['ReportingStatus'] == "Submitted") | (has_ghg_intensity['ReportingStatus'] == "Submitted Data")].copy()

    # FIlter building data by year, leaving only records with the most recent year
    all_submitted_data = all_submitted_data.sort_values(by=['ID', 'DataYear'])
    all_recent_submitted_data = all_submitted_data.drop_duplicates(subset=['ID'], keep='last').copy()

    # Mark columns that look like numbers but should be strings as such to prevent decimals showing
    # up (e.g. zipcode of 60614 or Ward 9)
    all_recent_submitted_data[string_cols] = building_data[string_cols].astype(str)

    # Mark columns as ints that should never show a decimal, e.g. Number of Buildings, Zipcode
    all_recent_submitted_data[int_cols] = building_data[int_cols].astype('Int64')
    all_recent_submitted_data.to_csv(data_directory+data_out_file, sep=',', encoding='utf-8', index=False)