from transformers import pipeline

# Cargar el pipeline de texto a texto con GPT-2
generator = pipeline('text-generation', model='gpt2')

prompt = "DataPM es una plataforma para"

result = generator(prompt, max_length=50, num_return_sequences=1)

print("\n--- Resultado GPT-2 ---")
print(result[0]['generated_text'])
