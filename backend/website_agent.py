#!/usr/bin/env python3
"""
AI Agent для генерации адаптивных сайтов
Оптимизированная версия для Fedora 42
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

class GenerationRequest(BaseModel):
    site_name: str
    description: str
    style: str = "modern"
    theme: str = "light"
    target_devices: List[str] = ["mobile", "tablet", "desktop"]
    seo_enabled: bool = True
    multi_language: bool = False
    images: List[Dict] = []

class GenerationResult(BaseModel):
    status: str
    site_name: str = ""
    generation_id: str = ""
    html_content: str = ""
    css_content: str = ""
    js_content: str = ""
    seo_meta: Dict[str, str] = {}
    images_used: List[str] = []
    generation_time: float = 0.0
    error_message: str = ""

class WebsiteGeneratorAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.base_prompt = self._load_base_prompt()
        self.responsive_breakpoints = {
            "mobile": "320px",
            "tablet": "768px", 
            "desktop": "1024px",
            "large": "1440px"
        }
        
    def _load_base_prompt(self) -> str:
        """Загрузка базового промпта для генерации"""
        return """
        Ты - senior frontend разработчик с 10+ лет опыта. Создавай современные, адаптивные веб-сайты которые идеально работают на всех устройствах.

        КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
        1. Mobile-first подход
        2. CSS Grid/Flexbox для адаптивности
        3. Семантические HTML5 теги
        4. Доступность (ARIA attributes)
        5. Оптимизация производительности
        6. SEO-дружественная структура

        CSS ТРЕБОВАНИЯ:
        - Использовать CSS переменные для цветов
        - Mobile-first media queries
        - Flexbox/Grid для layout
        - Плавные анимации
        - Темная/светлая тема поддержка
        - Modern CSS (grid, custom properties)

        ОБЯЗАТЕЛЬНЫЕ СЕКЦИИ:
        - Header с навигацией
        - Hero секция с CTA
        - Основной контент
        - Footer с контактами

        ВЕРНИ ТОЛЬКО JSON С СЛЕДУЮЩЕЙ СТРУКТУРОЙ:
        {
          "html": "полный HTML код",
          "css": "полный CSS код",
          "js": "JavaScript код (опционально)",
          "seo": {
            "title": "заголовок страницы",
            "description": "meta description", 
            "keywords": "ключевые слова"
          }
        }

        Не добавляй никакого пояснительного текста, только чистый JSON.
        """
    
    async def generate_website(self, request: GenerationRequest) -> GenerationResult:
        """Генерация адаптивного веб-сайта"""
        start_time = datetime.now()
        
        try:
            # Формирование промпта
            prompt = self._build_generation_prompt(request)
            
            # Вызов OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": self.base_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Парсинг ответа
            content = response.choices[0].message.content
            result_data = self._parse_response(content)
            
            # Оптимизация и адаптация
            optimized_html = self._optimize_html(result_data.get("html", ""), request.target_devices)
            optimized_css = self._optimize_css(result_data.get("css", ""), request.target_devices)
            js_content = result_data.get("js", "")
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GenerationResult(
                status="success",
                site_name=request.site_name,
                html_content=optimized_html,
                css_content=optimized_css,
                js_content=js_content,
                seo_meta=result_data.get("seo", {}),
                images_used=[img.get("url", "") for img in request.images],
                generation_time=generation_time
            )
            
        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            return GenerationResult(
                status="error",
                error_message=str(e),
                generation_time=generation_time
            )
    
    def _build_generation_prompt(self, request: GenerationRequest) -> str:
        """Построение промпта для генерации"""
        devices_text = ", ".join(request.target_devices)
        
        prompt = f"""
        СОЗДАЙ АДАПТИВНЫЙ ВЕБ-САЙТ:

        НАЗВАНИЕ САЙТА: {request.site_name}
        ОПИСАНИЕ: {request.description}
        СТИЛЬ ДИЗАЙНА: {request.style}
        ЦВЕТОВАЯ ТЕМА: {request.theme}
        ЦЕЛЕВЫЕ УСТРОЙСТВА: {devices_text}
        SEO ОПТИМИЗАЦИЯ: {'ДА' if request.seo_enabled else 'НЕТ'}
        МУЛЬТИЯЗЫЧНОСТЬ: {'ДА' if request.multi_language else 'НЕТ'}

        ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:
        - Mobile-first responsive design
        - Breakpoints: 320px, 768px, 1024px, 1440px
        - Semantic HTML5 markup
        - CSS Grid/Flexbox layouts
        - Accessible (ARIA labels)
        - Fast loading performance

        ДИЗАЙН ТРЕБОВАНИЯ:
        - Modern {request.style} style
        - {request.theme} color theme
        - Professional typography
        - Consistent spacing
        - Interactive elements

        ВКЛЮЧИ СЛЕДУЮЩИЕ СЕКЦИИ:
        1. Header с логотипом и навигацией
        2. Hero секция с основным заголовком
        3. Features/About секция
        4. Contact/form секция
        5. Footer с социальными ссылками

        ДОПОЛНИТЕЛЬНО:
        - Используй современные CSS техники
        - Добавь плавные переходы
        - Сделай код чистым и комментированным

        ВЕРНИ JSON С HTML, CSS И SEO МЕТАДАННЫМИ.
        """
        
        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Парсинг ответа от ИИ"""
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON ответа: {e}")
    
    def _optimize_html(self, html: str, target_devices: List[str]) -> str:
        """Оптимизация HTML для адаптивности"""
        # Добавление viewport meta tag
        if "viewport" not in html.lower():
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            html = html.replace("</head>", f"{viewport_meta}\n</head>", 1)
        
        # Оптимизация изображений
        html = html.replace("<img", '<img loading="lazy"')
        
        # Добавление базовой семантической структуры
        if "<main>" not in html:
            html = html.replace("<body>", '<body>\n    <main>', 1)
            html = html.replace("</body>", '    </main>\n</body>', 1)
        
        return html
    
    def _optimize_css(self, css: str, target_devices: List[str]) -> str:
        """Оптимизация CSS для адаптивности"""
        base_css = """
        /* Fedora AI Generator - Base Responsive Styles */
        :root {
            --primary-color: #3b6ea5;
            --secondary-color: #77216F;
            --text-color: #2c2c2c;
            --bg-color: #ffffff;
            --mobile: 320px;
            --tablet: 768px;
            --desktop: 1024px;
            --large: 1440px;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        html {
            font-size: 16px;
            scroll-behavior: smooth;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            min-height: 100vh;
        }
        
        img {
            max-width: 100%;
            height: auto;
        }
        
        /* Mobile First Media Queries */
        @media (min-width: 768px) {
            html { font-size: 17px; }
        }
        
        @media (min-width: 1024px) {
            html { font-size: 18px; }
        }
        
        /* Accessibility */
        @media (prefers-reduced-motion: reduce) {
            * { animation-duration: 0.01ms !important; }
        }
        """
        
        return base_css + "\n" + css

# Глобальный экземпляр агента
website_agent = WebsiteGeneratorAgent()