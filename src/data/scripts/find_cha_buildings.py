import csv

found = []

with open("src/data/scripts/cha_building_names.txt") as f:
    looking_for = f.read().splitlines()
    with open("src/data/source/ChicagoEnergyBenchmarking.csv") as a:
        whole_file = list(csv.DictReader(a))

        for i, p in enumerate(looking_for):
            for j, whole_file_line in enumerate(whole_file):
                if p.lower().strip().replace(" ", "") in whole_file_line["Property Name"].lower().strip().replace(" ", ""):
                    found.append((whole_file_line["ID"], whole_file_line["Property Name"]))
                    break

for place in found:
    print('// '+place[1])
    print("'" + place[0] + "'" + ": { owner: BuildingOwners.cha.key },")