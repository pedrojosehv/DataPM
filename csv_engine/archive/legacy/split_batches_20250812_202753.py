import csv
import os

def split_csv_batches(input_path, output_dir, batch_size=10):
    os.makedirs(output_dir, exist_ok=True)
    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = list(csv.reader(infile))
        header = reader[0]
        rows = reader[1:]
        total = len(rows)
        for i in range(0, total, batch_size):
            batch_rows = rows[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            out_path = os.path.join(
                output_dir,
                f"20250812_202753_DataPM_result_batch_{batch_num}.csv"
            )
            with open(out_path, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(header)
                writer.writerows(batch_rows)
            print(f"Batch {batch_num} written: {out_path}")

if __name__ == "__main__":
    split_csv_batches(
        r"d:\Work Work\Upwork\DataPM\csv\src\csv_processed\20250812_202753_DataPM_result.csv",
        r"d:\Work Work\Upwork\DataPM\csv\src\csv_processed",
        batch_size=10
    )
