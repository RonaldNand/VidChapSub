import csv

with open("timestamp.csv") as csv_file:
    csv_reader = csv.DictReader(csv_file)

    # csv_reader = csv.reader(csv_file)

    for row in csv_reader:
        print(row)
        print(row['Chapter'])