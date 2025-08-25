import csv

input_file = 'linkedin_jobs_detailed.csv'
output_file = 'linkedin_jobs_detailed_head5.csv'

with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    rows = [next(reader) for _ in range(6)]  # header + 5 rows

with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerows(rows)
