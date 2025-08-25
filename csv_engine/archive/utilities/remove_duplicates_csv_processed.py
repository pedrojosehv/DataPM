
import os
import pandas as pd
from datetime import datetime

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), 'csv', 'src', 'csv_processed')
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_PATH = os.path.join(PROCESSED_DIR, f'remove_duplicates_log_{timestamp}.csv')

# Recolectar todos los archivos CSV (ignorando subcarpetas)
csv_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.csv') and os.path.isfile(os.path.join(PROCESSED_DIR, f))]

# Leer y concatenar todos los archivos, agregando columna de origen
df_list = []
for fname in csv_files:
    path = os.path.join(PROCESSED_DIR, fname)
    df = pd.read_csv(path)
    df['__source_file'] = fname
    df_list.append(df)

df_all = pd.concat(df_list, ignore_index=True)

# Detectar duplicados (todas las filas duplicadas excepto la primera)
duplicates = df_all.duplicated(subset=['Job title (original)', 'Company'], keep='first')
df_dupes = df_all[duplicates].copy()

# Guardar log de duplicados eliminados (siempre genera el archivo, aunque esté vacío)
if not df_dupes.empty:
    df_dupes.to_csv(LOG_PATH, index=False)
else:
    # Si no hay duplicados, guardar solo encabezados
    cols = df_all.columns.tolist()
    pd.DataFrame(columns=cols).to_csv(LOG_PATH, index=False)

# Eliminar duplicados por Job title (original) + Company, manteniendo la primera aparición
df_dedup = df_all.drop_duplicates(subset=['Job title (original)', 'Company'], keep='first')

# Limpiar archivos originales y reescribir sólo filas únicas correspondientes a cada archivo
for fname in csv_files:
    path = os.path.join(PROCESSED_DIR, fname)
    df_file = df_dedup[df_dedup['__source_file'] == fname].drop(columns=['__source_file'])
    df_file.to_csv(path, index=False)

print('✔️ Duplicados eliminados por Job title (original) + Company en todos los CSVs. Log generado.')
