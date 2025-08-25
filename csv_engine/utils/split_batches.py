import csv
import os

def split_csv_batches(input_path, output_dir, batch_size=10):
    os.makedirs(output_dir, exist_ok=True)
    # Crear carpeta archive si no existe
    archive_dir = os.path.join(os.path.dirname(output_dir), 'archive')
    os.makedirs(archive_dir, exist_ok=True)
    # Leer y dividir en batches
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
                f"20250814_215758_DataPM_result_batch_{batch_num}.csv"
            )
            with open(out_path, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(header)
                writer.writerows(batch_rows)
            print(f"Batch {batch_num} written: {out_path}")
    # Mover archivo original a archive
    import shutil
    shutil.move(input_path, os.path.join(archive_dir, os.path.basename(input_path)))
    print(f"Archivo original movido a archive: {os.path.join(archive_dir, os.path.basename(input_path))}")

if __name__ == "__main__":
    split_csv_batches(
        r"d:\Work Work\Upwork\DataPM\csv\archive\20250814_215758_DataPM_result.csv",
        r"d:\Work Work\Upwork\DataPM\src\csv_processed",
        batch_size=10
    )
