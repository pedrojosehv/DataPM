import os
import pandas as pd

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), 'csv', 'src', 'csv_processed')
NOT_NORMALIZED_DIR = os.path.abspath(os.path.join(PROCESSED_DIR, '..', 'not_normalized'))
os.makedirs(NOT_NORMALIZED_DIR, exist_ok=True)
LOG_PATH = os.path.join(NOT_NORMALIZED_DIR, 'remove_duplicates_log.csv')

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

# Guardar log de duplicados eliminados
if not df_dupes.empty:
    df_dupes.to_csv(LOG_PATH, index=False)
    print(f'Log de duplicados guardado en: {LOG_PATH}')
else:
    print('No se encontraron duplicados para loguear.')
