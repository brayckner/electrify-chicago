import json
import logging
import pandas

from typing import List
from src.data.scripts.utils import get_and_clean_csv, json_data_builder, get_data_file_path
from src.data.scripts.building_utils import clean_property_name

# Assume run in /data
data_directory = 'source'
data_out_directory = 'dist'

# The /debug directory is to have a well formatted JSON for reading
data_debug_directory = 'debug'

# Gatsby doesn't like spaces so we use a CSV with renamed headers with no units
building_emissions_file = 'ChicagoEnergyBenchmarkingAllNewestInstances.csv'
building_emissions_file_out_name = 'building-benchmarks'

# Columns we want to run statistical analysis and ranking on - order matters here
building_cols_to_analyze = [
    'GHGIntensity',
    'TotalGHGEmissions',
    'ElectricityUse',
    'FossilGasUse',
    'SourceEUI',
    'SiteEUI',
    'YearBuilt',
    'GrossFloorArea',
    'DistrictSteamUse',
    'DistrictChilledWaterUse'
]

# Columns we want to rank for and append ranks to each building's data
building_cols_to_rank = [
    'GHGIntensity',
    'TotalGHGEmissions',
    'ElectricityUse',
    'FossilGasUse',
    'GrossFloorArea',
    'SourceEUI',
    'SiteEUI',
]

# Columns that should be strings because they are immutable identifiers
string_cols = [
    'PropertyName',
    'ChicagoEnergyRating',
    'ZIPCode',
]

# Int columns that are numbers (and can get averaged) but should be rounded
int_cols = [
    'NumberOfBuildings',
    'ENERGYSTARScore',
    # TODO: Move to string after figuring out why the X.0 is showing up
    'Wards',
    'CensusTracts',
    'CommunityAreas',
    'HistoricalWards2003-2015'
]

# Calculates overall stats for all buildings and outputs them into a keyed JSON file. Used to show
# median values for fields
# Returns the output file if succeeds
def calculateBuildingStats(building_data_in: pandas.DataFrame) -> str:
    # Clone the input data to prevent manipulating it on accident
    building_data = building_data_in.copy()

    benchmark_stats_df = pandas.DataFrame()

    # The details columns we want to keep. Note that 50% = median
    detail_cols_to_keep = ['count', 'mean', 'std', 'min', 'max', '25%', '50%', '75%']

    benchmark_stats_df = building_data[building_cols_to_analyze].describe(
    ).loc[detail_cols_to_keep]

    # Round all data to an int, all of the building data is pretty large values so the precision
    # isn't reasonable for statistical analysis
    benchmark_stats_df = benchmark_stats_df.round(1)

    # Rename columns to work with GraphQL (no numbers like '25%')
    # Rename 50% to median since those tqo are equivalent
    benchmark_stats_df.rename(index={
        '25%': 'twentyFifthPercentile',
        '50%': 'median',
        '75%': 'seventyFifthPercentile',
    }, inplace=True)

    # Write out the data
    filename = 'building-benchmark-stats.json'

    outputted_path = get_data_file_path(data_out_directory, filename)

    # Get the unique primary property types, so the FE can show it as a filter
    list_of_types = building_data.PrimaryPropertyType.unique()

    print('Available Primary Types: (copy to data/property-types.json)')
    print(list_of_types.tolist())

    # Write the minified JSON to the dist directory and indented JSON to the debug directory
    benchmark_stats_df.to_json(outputted_path)
    benchmark_stats_df.to_json(str(get_data_file_path(data_debug_directory, filename)),
                               indent=4)

    return outputted_path


# Returns the output file path if it succeeds
def processBuildingData() -> List[str]:
    # Store files we write out to
    outputted_paths = []

    building_data = get_and_clean_csv(get_data_file_path(data_directory, building_emissions_file))

    # Convert our columns to analyze to numeric data by stripping commas, otherwise the rankings
    # are junk
    building_data[building_cols_to_analyze] = building_data[building_cols_to_analyze].apply(
        lambda x: pandas.to_numeric(x.astype(str).str.replace(',', ''), errors='coerce'))

    # Mark columns that look like numbers but should be strings as such to prevent decimals showing
    # up (e.g. zipcode of 60614 or Ward 9)
    building_data[string_cols] = building_data[string_cols].astype(str)

    # Mark columns as ints that should never show a decimal, e.g. Number of Buildings, Zipcode
    building_data[int_cols] = building_data[int_cols].astype('Int64')

    building_data['PropertyName'] = building_data['PropertyName'].map(clean_property_name)

    # find the latest year in the data
    latest_year = building_data['DataYear'].max()

    # filter out all buildings that aren't the latest year
    latest_building_data = building_data[building_data['DataYear'] == latest_year]

    outputted_paths.append(calculateBuildingStats(latest_building_data))

    # Loop through building_cols_to_rank and calculate both a numeric rank (e.g. #1 highest GHG
    # Intensity) and a percentage (e.g. top 95% of total GHG emissions)
    # We use descending on all columns so the biggest emitters are #1, we'll make a separate column
    # for descending ranks
    # E.g Keating Hall is the #1 building by GHG Intensity, and lowest 25th percentile in footprint
    for col in building_cols_to_rank:
        building_data[col + 'Rank'] = building_data.where(building_data['DataYear'] == latest_year)[col].rank(ascending=False)

        # The percentile rank can be ascending, we want to say this building is worse than X% of buildings
        building_data[col + 'PercentileRank'] = building_data.where(building_data['DataYear'] == latest_year)[col].rank(pct=True).round(3)

    # Export the data
    output_path = get_data_file_path(data_out_directory, building_emissions_file_out_name + '.csv')

    building_data.to_csv(output_path, sep=',', encoding='utf-8', index=False)

    outputted_paths.append(output_path)

    debug_json_data = json_data_builder(
        building_data, 'building_benchmarks', is_array=True, array_key="building_benchmarks")

    # We write out files to a /debug directory that is .gitignored with indentation to
    # make it readable but to not have to store giant files
    with open(
            data_debug_directory + '/' + building_emissions_file_out_name + '.json', 'w', encoding='utf-8') as f:
        json.dump(debug_json_data, f, ensure_ascii=True, indent=4)

    return outputted_paths


if __name__ == '__main__':
    print("Starting data processing, this may take a few seconds...")

    outputted_paths = []

    outputted_paths = outputted_paths + processBuildingData()

    print("\nData processing done! Files exported: ")

    for path in outputted_paths:
        if path:
            # made sure to convert path:PosixPath to str
            print('- ' + str(path))

    print('\nFor more understandable data, see \'data/debug\' directory')

    print('\nNote: You must restart `gridsome develop` for data changes to take effect.')
