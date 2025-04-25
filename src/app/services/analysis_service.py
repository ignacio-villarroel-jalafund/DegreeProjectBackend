import ollama
from app.core.config import settings
from typing import Dict, Optional

class AnalysisService:
    def __init__(self, model_name: str = settings.OLLAMA_MODEL, host: str = settings.OLLAMA_HOST):
        self.model_name = model_name
        self.client = ollama.Client(host=host)
        try:
            self.client.list()
            print(f"Conexión inicial con Ollama en {host} exitosa.")
        except Exception as e:
            print(f"Advertencia: No se pudo conectar con Ollama ({host}) al iniciar: {e}")

    def analyze_recipe(self, scraped_data: Dict) -> Optional[str]:
        """Analiza los datos scrapeados de una receta usando Ollama."""
        if not scraped_data or not scraped_data.get('recipe_name'):
            print("\nNo hay datos suficientes para analizar (faltan título o datos).")
            return None

        print(f"\nUsando {self.model_name} para analizar la receta: '{scraped_data['recipe_name']}'...")

        summary_parts = [f"Nombre: {scraped_data.get('recipe_name', 'N/A')}"]
        if scraped_data.get('ingredients'):
             summary_parts.append(f"Ingredientes: {', '.join(scraped_data['ingredients'])}")
        if scraped_data.get('directions'):
             summary_parts.append(f"Número de pasos: {len(scraped_data['directions'])}")

        summary = "\n".join(summary_parts)

        prompt = f"""
        Eres un asistente de cocina experto y conciso que habla español de Bolivia.
        Analiza la siguiente receta y proporciona un resumen breve (3-5 puntos clave) sobre:

        1. Dificultad estimada (ej. Fácil, Media, Difícil) y por qué.
        2. Ocasión ideal (ej. Diario rápido, Fin de semana, Ocasión especial).
        3. Posibles variaciones o acompañamientos sugeridos.
        4. Algún ingrediente o técnica destacable (si aplica).
        5. Consejo práctico para prepararla.

        Receta:
        {summary}

        **Instrucciones de formato:**  
        - Responde **solo** con la lista numerada de los 5 puntos solicitados.  
        - Al final, incluye únicamente la frase **“¡Buen provecho!”**.  
        - **No** añadas saludos, introducciones ni texto extra.
        """
        try:
            response = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            options={'temperature': 0.6}
            )
            analysis_text = response.get('response', '').strip()
            print(f"Análisis completado.")
            return analysis_text
        except Exception as e:
            print(f"Error en el análisis con {self.model_name}: {e}")
            return None

analysis_service = AnalysisService()