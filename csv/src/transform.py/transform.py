import pandas as pd
import re

# --- Funciones de Normalización ---
# Estas funciones usan los vocabularios controlados que definimos.

def normalize_job_title(title):
    """
    Normaliza el título del rol a un conjunto fijo de valores.
    """
    normalized_titles = {
        "Product Designer": "UI/UX Designer",
        "UX & Product Designer": "UI/UX Designer",
        "Mobile Product Designer (UI/UX)": "UI/UX Designer",
        "Process Designer SDLC": "Process Designer",
        "Product Compliance Junior sector de automoción": "Other",
        "Consultor de Proyecto/Analista Funcional. Sector Salud": "Business Analyst",
        "Remote Industrial/Product Designer (Freelance Collaboration)": "Product Designer",
        "Data Analyst": "Data Analyst",
        "Product Manager": "Product Manager"
    }
    for key, value in normalized_titles.items():
        if key.lower() in title.lower():
            return value
    return "Other"

def normalize_experience(experience):
    """
    Normaliza la experiencia a un formato estandarizado (ej. "3-5", "5+", "0-3").
    """
    if not isinstance(experience, str):
        return "Unknown"
    
    if "0-1" in experience:
        return "0-3"
    elif "3+" in experience:
        return "3-5"
    elif "5+" in experience:
        return "5+"
    elif "3-5" in experience:
        return "3-5"
    return "Unknown"

def normalize_location(location):
    """
    Divide la ubicación en Ciudad, Estado y País.
    """
    city, state, country = "Unknown", "Unknown", "Unknown"
    
    # Lista de países conocidos
    countries = {
        "Spain": ["Madrid"],
        "European Union": [],
        "Panamá": [],
        "Venezuela": [],
        "United States": []
    }
    
    # Manejar el caso de 'NaN' o valores no válidos
    if not isinstance(location, str):
        return "Unknown", "Unknown", "Unknown"

    parts = [part.strip() for part in location.split(',')]
    
    # Lógica para determinar el país
    for country_name in countries.keys():
        if country_name in location:
            country = country_name
            break
            
    if country == "Unknown":
        return "Unknown", "Unknown", "Unknown"

    if len(parts) >= 3:
        city = parts[0]
        state = parts[1]
        country = parts[2]
    elif len(parts) == 2:
        if parts[1].strip().lower() in ["spain", "european union"]:
            city = parts[0]
            country = parts[1]
        else:
            city = parts[0]
            state = parts[1]
    elif len(parts) == 1:
        city_or_country = parts[0].strip()
        if city_or_country in ["Spain", "European Union"]:
            country = city_or_country
        else:
            city = city_or_country
    
    return city, state, country

def normalize_array_column(column_data, valid_set):
    """
    Normaliza una columna de array (Skills, Software, Degrees) a valores fijos.
    Devuelve una cadena de texto separada por punto y coma.
    """
    if not isinstance(column_data, str) or pd.isna(column_data):
        return ""

    items = re.split(r';|,', column_data)
    normalized_items = []
    
    for item in items:
        item = item.strip()
        if item:
            found = False
            for normalized_value in valid_set:
                if normalized_value.lower() in item.lower():
                    normalized_items.append(normalized_value)
                    found = True
                    break
    
    # Unir los elementos en una cadena separada por punto y coma
    return ';'.join(sorted(list(set(normalized_items))))

# --- Carga de datos ---
try:
    df = pd.read_csv('20250811_113942_ DataPM_result.csv')
except FileNotFoundError:
    print("Error: El archivo CSV no se encontró. Asegúrate de que está en el mismo directorio que el script.")
    exit()

# --- Vocabularios controlados (conjuntos fijos) ---
NORMALIZED_DEGREES = {
    "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
    "Higher Education", "Engineering", "Automotive Engineering", 
    "Vocational Training", "Other"
}
NORMALIZED_SKILLS = {
    "SQL", "Python", "R", "C", "C++", "Java", "JavaScript", "Excel", 
    "Project Management", "Agile", "Scrum", "API", "Cloud Computing", 
    "Machine Learning", "Data Analysis", "Data Visualization", 
    "User Research", "UI/UX Design", "Product Design", 
    "Product Management", "Marketing", "Sales", "Communication", 
    "Problem Solving", "Process Optimization", "Regulatory Compliance", 
    "Document Management", "Quality Control", "Auditing", 
    "Technical Writing", "Statistical Reporting", "Business Acumen", 
    "Cross-functional Collaboration", "Team Leadership", 
    "Healthcare Knowledge", "Supply Chain", "SDLC", 
    "User-Centered Design"
}
NORMALIZED_SOFTWARE = {
    "Figma", "Sketch", "Adobe XD", "Tableau", "Power BI", 
    "Microsoft Excel", "Jira", "Confluence", "Atlassian", "SAP", 
    "Salesforce", "HubSpot", "Google Analytics", "GitHub", "GitLab", 
    "DevOps Tools", "Vercel", "Next.js", "Prisma", "PlanetScale", 
    "Rhino", "Keyshot", "SolidWorks", "C4D", "OneDrive", "Word", 
    "IMDS", "Pytorch"
}

# --- Transformación de datos ---
print("Iniciando la transformación de datos...")

# Creamos un DataFrame vacío para los resultados
transformed_data = []

for index, row in df.iterrows():
    job_title_short = normalize_job_title(row['Role'])
    experience_years = normalize_experience(str(row['Experience']))
    job_schedule_type = "Unknown"
    seniority = str(row['Seniority']) if pd.notna(row['Seniority']) else "Unknown"
    city, state, country = normalize_location(str(row['Location']))
    
    # Normalizamos los arrays y los unimos en una cadena delimitada por ;
    skills = normalize_array_column(row['Skills'], NORMALIZED_SKILLS)
    degrees = normalize_array_column(row['Degrees'], NORMALIZED_DEGREES)
    software = normalize_array_column(row['Software'], NORMALIZED_SOFTWARE)
    
    # Preparamos la nueva fila con los datos transformados
    new_row = {
        'job_title_original': row['Role'],
        'job_title_short': job_title_short,
        'experience_years': experience_years,
        'job_schedule_type': job_schedule_type,
        'seniority': seniority,
        'city': city,
        'state': state,
        'country': country,
        'company_name': row['Company'],
        'degrees': degrees,
        'skills': skills,
        'software': software
    }
    
    transformed_data.append(new_row)

# Creamos un nuevo DataFrame con los datos transformados
transformed_df = pd.DataFrame(transformed_data)

# Guardamos el resultado en un nuevo archivo CSV
output_filename = "data_pm_transformed.csv"
transformed_df.to_csv(output_filename, index=False)

print(f"Transformación completada. El archivo '{output_filename}' ha sido guardado.")

# Opcional: imprimir las primeras 5 filas para una vista previa
print("\nVista previa de los datos transformados:")
print(transformed_df.head().to_markdown(index=False, numalign="left", stralign="left"))
