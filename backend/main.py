#!/usr/bin/env python3
"""
Fedora AI Website Generator - Оптимизированный бэкенд
Версия 4.0.0 для Fedora 42
"""

import os
import sys
import json
import time
import asyncio
import zipfile
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import redis
from dotenv import load_dotenv

from website_agent import WebsiteGeneratorAgent, GenerationRequest, GenerationResult
from image_processor import ImageProcessor

# Загрузка переменных окружения
load_dotenv()

# Модели данных
class WebsiteConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    style: str = Field("modern", regex="^(modern|classic|minimal|creative)$")
    theme: str = Field("light", regex="^(light|dark|auto)$")
    target_devices: List[str] = Field(["mobile", "tablet", "desktop"])
    seo_enabled: bool = True
    multi_language: bool = False

class GenerationStatus(BaseModel):
    generation_id: str
    status: str
    progress: float = 0.0
    message: str = ""
    result_url: Optional[str] = None
    error: Optional[str] = None

class FedoraWebsiteGenerator:
    def __init__(self):
        self.app = None
        self.redis_client = None
        self.agent = None
        self.image_processor = None
        self.start_time = time.time()
        
    async def initialize(self):
        """Асинхронная инициализация приложения"""
        self.app = FastAPI(
            title="Fedora AI Website Generator Pro",
            description="AI-powered responsive website generator for Fedora 42",
            version="4.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            lifespan=self.lifespan
        )
        
        await self.setup_middleware()
        await self.setup_directories()
        await self.setup_redis()
        await self.setup_routes()
        
        # Инициализация компонентов
        self.agent = WebsiteGeneratorAgent()
        self.image_processor = ImageProcessor()
        
        return self.app
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Управление жизненным циклом приложения"""
        # Startup
        print("🚀 Запуск Fedora AI Website Generator...")
        await self.setup_directories()
        await self.setup_redis()
        
        yield
        
        # Shutdown
        print("🛑 Остановка Fedora AI Website Generator...")
        if self.redis_client:
            self.redis_client.close()
    
    async def setup_middleware(self):
        """Настройка middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    async def setup_directories(self):
        """Создание необходимых директорий"""
        self.base_dir = Path(__file__).parent
        directories = [
            "uploads/images",
            "uploads/temp",
            "generated/sites", 
            "generated/zips",
            "cache/redis",
            "logs/app",
            "logs/access",
            "static/assets",
            "static/templates"
        ]
        
        for dir_path in directories:
            full_path = self.base_dir / ".." / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    async def setup_redis(self):
        """Настройка Redis соединения"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Тестирование соединения
            self.redis_client.ping()
            print("✅ Redis подключен успешно")
        except redis.ConnectionError as e:
            print(f"⚠️ Redis недоступен: {e}")
            self.redis_client = None
    
    async def setup_routes(self):
        """Настройка маршрутов API"""
        
        # Статические файлы
        static_path = self.base_dir / ".." / "static"
        self.app.mount("/static", StaticFiles(directory=static_path), name="static")
        
        generated_path = self.base_dir / ".." / "generated" / "sites"
        self.app.mount("/sites", StaticFiles(directory=generated_path), name="sites")
        
        # API маршруты
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            return {"message": "Fedora AI Website Generator API", "version": "4.0.0"}
        
        @self.app.get("/api/health")
        async def health_check():
            """Проверка здоровья системы"""
            redis_status = "connected" if self.redis_client and self.redis_client.ping() else "disconnected"
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "4.0.0",
                "system": {
                    "platform": sys.platform,
                    "python_version": sys.version,
                    "uptime": round(time.time() - self.start_time, 2)
                },
                "services": {
                    "redis": redis_status,
                    "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
                },
                "resources": await self.get_system_resources()
            }
        
        @self.app.post("/api/generate", response_model=GenerationStatus)
        async def generate_website(
            background_tasks: BackgroundTasks,
            site_name: str = Form(..., min_length=1, max_length=100),
            description: str = Form(..., min_length=10, max_length=1000),
            style: str = Form("modern"),
            theme: str = Form("light"),
            target_devices: List[str] = Form(["mobile", "tablet", "desktop"]),
            seo_enabled: bool = Form(True),
            multi_language: bool = Form(False),
            images: List[UploadFile] = File(None)
        ):
            """Генерация адаптивного веб-сайта"""
            try:
                # Валидация входных данных
                if not all(device in ["mobile", "tablet", "desktop"] for device in target_devices):
                    raise HTTPException(400, "Некорректные целевые устройства")
                
                # Создание ID генерации
                generation_id = hashlib.sha256(
                    f"{site_name}{description}{style}{time.time()}".encode()
                ).hexdigest()[:16]
                
                # Проверка кэша
                cache_key = f"generation:{hashlib.md5(f'{site_name}{description}{style}'.encode()).hexdigest()}"
                if self.redis_client:
                    cached = self.redis_client.get(cache_key)
                    if cached:
                        cached_data = json.loads(cached)
                        return GenerationStatus(
                            generation_id=generation_id,
                            status="completed",
                            progress=100.0,
                            message="Результат загружен из кэша",
                            result_url=f"/sites/{generation_id}/index.html"
                        )
                
                # Обработка изображений
                processed_images = []
                if images:
                    for image in images:
                        if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
                            raise HTTPException(400, f"Неподдерживаемый формат изображения: {image.content_type}")
                        
                        processed = await self.image_processor.process_upload(image)
                        processed_images.append(processed)
                
                # Создание запроса генерации
                request = GenerationRequest(
                    site_name=site_name,
                    description=description,
                    style=style,
                    theme=theme,
                    target_devices=target_devices,
                    seo_enabled=seo_enabled,
                    multi_language=multi_language,
                    images=processed_images
                )
                
                # Запуск фоновой задачи
                background_tasks.add_task(
                    self.process_generation,
                    generation_id,
                    request,
                    cache_key
                )
                
                return GenerationStatus(
                    generation_id=generation_id,
                    status="processing",
                    progress=0.0,
                    message="Генерация сайта начата"
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f"Ошибка при запуске генерации: {str(e)}")
        
        @self.app.get("/api/generation/{generation_id}", response_model=GenerationStatus)
        async def get_generation_status(generation_id: str):
            """Получение статуса генерации"""
            if self.redis_client:
                status_key = f"status:{generation_id}"
                status_data = self.redis_client.get(status_key)
                if status_data:
                    return GenerationStatus(**json.loads(status_data))
            
            # Проверка файловой системы
            site_dir = self.base_dir / ".." / "generated" / "sites" / generation_id
            if site_dir.exists() and (site_dir / "index.html").exists():
                return GenerationStatus(
                    generation_id=generation_id,
                    status="completed",
                    progress=100.0,
                    message="Генерация завершена",
                    result_url=f"/sites/{generation_id}/index.html"
                )
            
            raise HTTPException(404, "Генерация не найдена")
        
        @self.app.get("/api/download/{generation_id}")
        async def download_website(generation_id: str, format: str = "zip"):
            """Скачивание сгенерированного сайта"""
            site_dir = self.base_dir / ".." / "generated" / "sites" / generation_id
            zip_dir = self.base_dir / ".." / "generated" / "zips"
            
            if not site_dir.exists():
                raise HTTPException(404, "Сайт не найден")
            
            if format == "zip":
                zip_path = zip_dir / f"{generation_id}.zip"
                if not zip_path.exists():
                    await self.create_zip_archive(generation_id, site_dir, zip_path)
                
                return FileResponse(
                    zip_path,
                    filename=f"website_{generation_id}.zip",
                    media_type='application/zip'
                )
            else:
                index_path = site_dir / "index.html"
                return FileResponse(index_path, filename="index.html")
        
        @self.app.get("/api/templates")
        async def get_available_templates():
            """Получение доступных шаблонов"""
            return [
                {
                    "id": "modern-business",
                    "name": "Современный бизнес",
                    "description": "Корпоративный сайт с адаптивным дизайном",
                    "category": "business",
                    "preview": "/static/templates/business-preview.jpg",
                    "styles": ["modern", "professional"]
                },
                {
                    "id": "portfolio-creative", 
                    "name": "Портфолио креатив",
                    "description": "Портфолио для дизайнеров и фотографов",
                    "category": "portfolio",
                    "preview": "/static/templates/portfolio-preview.jpg",
                    "styles": ["creative", "minimal"]
                },
                {
                    "id": "ecommerce-minimal",
                    "name": "Интернет-магазин", 
                    "description": "Минималистичный магазин с корзиной",
                    "category": "ecommerce",
                    "preview": "/static/templates/ecommerce-preview.jpg",
                    "styles": ["minimal", "modern"]
                }
            ]
    
    async def process_generation(self, generation_id: str, request: GenerationRequest, cache_key: str):
        """Фоновая обработка генерации сайта"""
        try:
            # Обновление статуса
            await self.update_generation_status(generation_id, "processing", 25.0, "Генерация контента...")
            
            # Генерация сайта
            result = await self.agent.generate_website(request)
            
            await self.update_generation_status(generation_id, "processing", 75.0, "Оптимизация кода...")
            
            # Сохранение результата
            await self.save_generation_result(generation_id, result)
            
            # Кэширование результата
            if self.redis_client:
                self.redis_client.setex(
                    cache_key,
                    timedelta(hours=24),
                    json.dumps({
                        "generation_id": generation_id,
                        "result_url": f"/sites/{generation_id}/index.html"
                    })
                )
            
            await self.update_generation_status(
                generation_id, 
                "completed", 
                100.0, 
                "Генерация завершена",
                f"/sites/{generation_id}/index.html"
            )
            
        except Exception as e:
            await self.update_generation_status(
                generation_id,
                "error",
                0.0,
                "Ошибка генерации",
                error=str(e)
            )
    
    async def update_generation_status(self, generation_id: str, status: str, progress: float, 
                                     message: str, result_url: str = None, error: str = None):
        """Обновление статуса генерации"""
        status_data = GenerationStatus(
            generation_id=generation_id,
            status=status,
            progress=progress,
            message=message,
            result_url=result_url,
            error=error
        )
        
        if self.redis_client:
            status_key = f"status:{generation_id}"
            self.redis_client.setex(
                status_key,
                timedelta(hours=1),
                status_data.json()
            )
    
    async def save_generation_result(self, generation_id: str, result: GenerationResult):
        """Сохранение результата генерации"""
        site_dir = self.base_dir / ".." / "generated" / "sites" / generation_id
        site_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохранение HTML
        if result.html_content:
            (site_dir / "index.html").write_text(result.html_content, encoding='utf-8')
        
        # Сохранение CSS
        if result.css_content:
            (site_dir / "styles.css").write_text(result.css_content, encoding='utf-8')
        
        # Сохранение JavaScript
        if result.js_content:
            (site_dir / "script.js").write_text(result.js_content, encoding='utf-8')
        
        # Сохранение метаданных
        meta_data = {
            "generation_id": generation_id,
            "site_name": result.site_name,
            "created_at": datetime.now().isoformat(),
            "generation_time": result.generation_time,
            "seo_meta": result.seo_meta,
            "images_used": result.images_used
        }
        
        (site_dir / "meta.json").write_text(
            json.dumps(meta_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    async def create_zip_archive(self, generation_id: str, site_dir: Path, zip_path: Path):
        """Создание ZIP архива"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in site_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(site_dir)
                    zipf.write(file_path, arcname)
    
    async def get_system_resources(self):
        """Получение информации о системных ресурсах"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                "cpu_usage": cpu_percent,
                "memory": {
                    "total": round(memory.total / (1024 ** 3), 2),
                    "used": round(memory.used / (1024 ** 3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total": round(disk.total / (1024 ** 3), 2),
                    "used": round(disk.used / (1024 ** 3), 2),
                    "percent": disk.percent
                }
            }
        except ImportError:
            return {"error": "psutil не установлен"}

# Создание и инициализация приложения
generator = FedoraWebsiteGenerator()
app = None

async def get_app():
    """Получение инициализированного приложения"""
    global app
    if app is None:
        app = await generator.initialize()
    return app

if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "main:get_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        factory=True
    )
    