import re
from typing import Dict, Any, List, Optional

from sqlalchemy import JSON


class RecipeProcessorService:
    def __init__(self):
        self.SPAM_KEYWORDS: List[str] = [
            'blog', 'instagram', 'facebook', 'youtube', 'tiktok', 'pinterest',
            'sígueme', 'visita mi', 'suscríbete', '.com', 'http'
        ]
        self.CONVERSATIONAL_KEYWORDS: List[str] = [
            'yo', 'a mí', 'mi familia', 'nosotros', 'recuerdo que', 'les cuento',
            'mi truco', 'en mi caso', 'espero que les guste', 'espero lo disfruten',
            'esta receta es', 'pueden encontrar'
        ]
        self.INSTRUCTION_VERBS: List[str] = [
            'añade', 'agrega', 'bate', 'calienta', 'corta', 'coce', 'cocina', 'coloca',
            'combina', 'deja', 'disuelve', 'divide', 'empana', 'engrasa', 'enrolla', 'enfría',
            'escurre', 'extiende', 'fríe', 'hierve', 'hornea', 'incorpora', 'lava', 'licúa', 'licua',
            'marina', 'mezcla', 'pela', 'pica', 'precalienta', 'prepara', 'remueve', 'retira',
            'salpimienta', 'sazona', 'sirve', 'sofríe', 'tamiza', 'tosta', 'unta', 'vierte',
            'en un vaso', 'batimos', 'precalentamos', 'metemos', 'vertemos', 'derretimos', 
        ]

    def _remove_emojis(self, text: str) -> str:
        if not text:
            return ""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F700-\U0001F77F"
            "\U0001FA70-\U0001FAFF"
            "\U00002702-\U000027B0"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def _clean_whitespace(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def _clean_and_format_text(self, text: str) -> str:
        text_no_emojis = self._remove_emojis(text)
        text_clean = self._clean_whitespace(text_no_emojis)
        return text_clean.capitalize()

    def _extract_yield_number(self, text: str) -> Optional[int]:
        if not text:
            return None
        match = re.search(r'\d+', text)
        if match:
            return int(match.group(0))
        return None

    def _filter_noisy_steps(self, steps: List[str]) -> List[str]:
        filtered_steps = []
        for step in steps:
            step_lower = step.lower()
            if any(keyword in step_lower for keyword in self.SPAM_KEYWORDS):
                continue

            is_direct_instruction = any(step_lower.startswith(
                verb) for verb in self.INSTRUCTION_VERBS)
            is_conversational = any(
                keyword in step_lower for keyword in self.CONVERSATIONAL_KEYWORDS)

            if is_conversational and not is_direct_instruction:
                continue

            filtered_steps.append(step)
        return filtered_steps

    def process(self, scraper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not scraper:
            return None

        try:
            title = self._clean_and_format_text(scraper.get('title'))
            image_url = scraper.get('image_url')
            yield_servings = self._extract_yield_number(
                scraper.get('servings'))
            time = scraper.get('time')

            ingredients = [self._clean_and_format_text(
                ing) for ing in scraper.get('ingredients')]

            raw_steps = [self._clean_and_format_text(
                step) for step in scraper.get('directions')]
            clean_steps = self._filter_noisy_steps(raw_steps)

            return {
                "title": title,
                "image_url": image_url,
                "servings": yield_servings,
                "time": time,
                "ingredients": ingredients,
                "directions": clean_steps,
                "url": scraper.get('url')
            }
        except Exception as e:
            print(f"An error occurred during data processing: {e}")


recipe_processor_service = RecipeProcessorService()
