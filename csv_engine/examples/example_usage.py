#!/usr/bin/env python3
"""
Ejemplo de uso de DataPM Processor
Muestra cómo procesar un registro de prueba sin necesidad de API key
"""

import os
import tempfile
import csv
from datapm_processor import DataPMProcessor

def create_sample_data():
    """Crea datos de muestra para demostración"""
    return [
        {
            'title': 'Senior Product Manager',
            'company': 'TechCorp Inc.',
            'location': 'San Francisco, CA',
            'description': '''We are seeking a Senior Product Manager to lead our product development team. 
            
Requirements:
- 5+ years of experience in product management
- Bachelor's degree in Business, Engineering, or related field
- Experience with Agile methodologies and Scrum
- Proficiency in SQL, Python, and data analysis tools
- Knowledge of cloud platforms (AWS, Azure)
- Experience with Jira, Confluence, and product management tools
- Strong communication and leadership skills

Responsibilities:
- Lead cross-functional teams in product development
- Conduct user research and market analysis
- Define product strategy and roadmap
- Work with engineering teams to deliver high-quality products
- Analyze product metrics and user feedback
- Collaborate with stakeholders across the organization

This is a full-time position with competitive salary and benefits.'''
        },
        {
            'title': 'UX/UI Designer Intern',
            'company': 'StartupXYZ',
            'location': 'Madrid, Spain',
            'description': '''Join our design team as a UX/UI Designer Intern!
            
What we're looking for:
- Currently pursuing or recently completed degree in Design, HCI, or related field
- Basic knowledge of design principles and user-centered design
- Familiarity with Figma, Adobe XD, or similar design tools
- Creative mindset and attention to detail
- Good communication skills
- Portfolio showing design projects (academic or personal)

What you'll do:
- Assist in user research and usability testing
- Create wireframes and prototypes
- Design user interfaces for web and mobile applications
- Collaborate with product managers and developers
- Learn about design systems and best practices

This is a 6-month internship program with potential for full-time conversion.'''
        }
    ]

def save_sample_csv(data, filename):
    """Guarda los datos de muestra en un CSV"""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['title', 'company', 'location', 'description']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    print(f"✅ Archivo de muestra creado: {filename}")

def demonstrate_processing():
    """Demuestra el procesamiento sin usar LLM real"""
    print("🚀 Demostración de DataPM Processor")
    print("=" * 50)
    
    # Crear datos de muestra
    sample_data = create_sample_data()
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    temp_file.close()
    
    # Guardar datos de muestra
    save_sample_csv(sample_data, temp_file.name)
    
    try:
        # Crear procesador (sin API key para demostración)
        processor = DataPMProcessor(llm_type="gemini", api_key="demo_key")
        
        # Leer CSV
        print("\n📖 Leyendo datos de muestra...")
        input_data = processor.read_csv(temp_file.name)
        print(f"✅ Leídos {len(input_data)} registros")
        
        # Mostrar datos de entrada
        print("\n📋 Datos de entrada:")
        for i, row in enumerate(input_data, 1):
            print(f"\nRegistro {i}:")
            print(f"  Título: {row['title']}")
            print(f"  Empresa: {row['company']}")
            print(f"  Ubicación: {row['location']}")
            print(f"  Descripción: {row['description'][:100]}...")
        
        # Simular procesamiento (sin llamar al LLM real)
        print("\n🤖 Simulando procesamiento con LLM...")
        print("(En uso real, esto llamaría a Gemini u Ollama)")
        
        # Crear datos de salida simulados
        simulated_output = []
        for i, row in enumerate(input_data):
            print(f"📝 Procesando registro {i+1}/{len(input_data)}")
            
            # Simular respuesta del LLM basada en el contenido
            if "Product Manager" in row['title']:
                job_title_short = "Product Manager"
                experience_years = "5+"
                seniority = "Senior"
                skills = ["Project Management", "Agile", "Scrum", "Data Analysis"]
                software = ["SQL", "Python", "Jira", "Confluence", "AWS", "Azure"]
            else:
                job_title_short = "UX/UI Designer"
                experience_years = "0-3"
                seniority = "Intern"
                skills = ["UI/UX Design", "User Research", "User-Centered Design"]
                software = ["Figma", "Adobe XD"]
            
            # Extraer ubicación
            location_parts = row['location'].split(', ')
            city = location_parts[0] if len(location_parts) > 0 else "Unknown"
            state = location_parts[1] if len(location_parts) > 1 else "Unknown"
            country = "United States" if state in ["CA", "NY", "TX"] else "Spain"
            
            processed_row = {
                'Job title (original)': row['title'],
                'Job title (short)': job_title_short,
                'Company': row['company'],
                'Country': country,
                'State': state,
                'City': city,
                'Schedule type': 'Full-time' if 'Senior' in row['title'] else 'Internship',
                'Experience years': experience_years,
                'Seniority': seniority,
                'Skills': '; '.join(skills),
                'Degrees': 'Bachelor\'s Degree',
                'Software': '; '.join(software)
            }
            
            simulated_output.append(processed_row)
        
        # Guardar resultados
        output_file = "csv/archive/demo_result.csv"
        processor.write_csv(simulated_output, output_file)
        
        # Mostrar resultados
        print("\n📊 Resultados del procesamiento:")
        for i, row in enumerate(simulated_output, 1):
            print(f"\nRegistro {i} procesado:")
            print(f"  Título original: {row['Job title (original)']}")
            print(f"  Título normalizado: {row['Job title (short)']}")
            print(f"  Empresa: {row['Company']}")
            print(f"  Ubicación: {row['City']}, {row['State']}, {row['Country']}")
            print(f"  Tipo: {row['Schedule type']}")
            print(f"  Experiencia: {row['Experience years']}")
            print(f"  Seniority: {row['Seniority']}")
            print(f"  Habilidades: {row['Skills']}")
            print(f"  Software: {row['Software']}")
        
        print(f"\n💾 Resultados guardados en: {output_file}")
        print("\n🎉 ¡Demostración completada!")
        
    except Exception as e:
        print(f"❌ Error en la demostración: {e}")
    
    finally:
        # Limpiar archivo temporal
        os.unlink(temp_file.name)

def show_usage_instructions():
    """Muestra instrucciones de uso"""
    print("\n" + "="*60)
    print("📚 INSTRUCCIONES DE USO REAL")
    print("="*60)
    
    print("\n1️⃣ CON GOOGLE GEMINI:")
    print("   python datapm_processor.py csv/linkedin_jobs_make.csv --llm gemini --api-key TU_API_KEY")
    
    print("\n2️⃣ CON OLLAMA:")
    print("   # Primero instala y ejecuta Ollama")
    print("   ollama serve")
    print("   python datapm_processor.py csv/linkedin_jobs_make.csv --llm ollama")
    
    print("\n3️⃣ SCRIPT INTERACTIVO:")
    print("   python run_datapm.py")
    
    print("\n4️⃣ CONFIGURAR API KEY:")
    print("   # Opción A: Variable de entorno")
    print("   set GEMINI_API_KEY=tu_api_key_aqui")
    print("   python datapm_processor.py datos.csv --llm gemini")
    
    print("\n   # Opción B: Proporcionar al ejecutar")
    print("   python datapm_processor.py datos.csv --llm gemini --api-key tu_api_key")
    
    print("\n🔗 Obtén tu API key de Gemini en:")
    print("   https://makersuite.google.com/app/apikey")

def main():
    """Función principal"""
    demonstrate_processing()
    show_usage_instructions()

if __name__ == "__main__":
    main()
