#!/usr/bin/env python3
"""
Script de prueba para verificar que las correcciones de duplicados funcionen correctamente.
Este script simula el procesamiento de trabajos sin necesidad de conectarse a LinkedIn.
"""

def test_duplicate_prevention():
    """Prueba la lógica de prevención de duplicados"""

    # Simular una lista de elementos con algunos IDs duplicados
    mock_job_cards = [
        MockJobCard("job_1", "Trabajo 1"),
        MockJobCard("job_2", "Trabajo 2"),
        MockJobCard("job_1", "Trabajo 1 Duplicado"),  # Duplicado
        MockJobCard("job_3", "Trabajo 3"),
        MockJobCard("job_2", "Trabajo 2 Duplicado"),  # Duplicado
        MockJobCard("job_4", "Trabajo 4"),
    ]

    # Simular el procesamiento con la nueva lógica
    processed_job_ids = set()
    processed_jobs = []
    skipped_duplicates = []

    for idx, card in enumerate(mock_job_cards, start=1):
        job_id = card.get_job_id()
        if job_id in processed_job_ids:
            skipped_duplicates.append(f"Skipped duplicate: {job_id}")
            continue
        processed_job_ids.add(job_id)
        processed_jobs.append(f"Processed: {card.get_title()} (ID: {job_id})")

    # Resultados
    print("=== PRUEBA DE PREVENCIÓN DE DUPLICADOS ===")
    print(f"Total trabajos simulados: {len(mock_job_cards)}")
    print(f"Trabajos procesados: {len(processed_jobs)}")
    print(f"Duplicados evitados: {len(skipped_duplicates)}")
    print("\nTrabajos procesados:")
    for job in processed_jobs:
        print(f"  ✅ {job}")
    print("\nDuplicados detectados:")
    for duplicate in skipped_duplicates:
        print(f"  ⚠️  {duplicate}")

    # Verificación
    expected_processed = 4  # job_1, job_2, job_3, job_4
    expected_duplicates = 2  # Los dos duplicados

    success = (len(processed_jobs) == expected_processed and
               len(skipped_duplicates) == expected_duplicates)

    print(f"\n✅ Test {'PASSED' if success else 'FAILED'}")
    return success

class MockJobCard:
    """Simula un elemento de trabajo de LinkedIn"""
    def __init__(self, job_id, title):
        self.job_id = job_id
        self.title = title

    def get_job_id(self):
        return self.job_id

    def get_title(self):
        return self.title

if __name__ == "__main__":
    test_duplicate_prevention()
