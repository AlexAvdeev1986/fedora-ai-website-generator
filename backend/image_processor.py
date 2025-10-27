#!/usr/bin/env python3
"""
Обработчик изображений для Fedora AI Website Generator
"""

import os
import aiofiles
from pathlib import Path
from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps

class ImageProcessor:
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP']
        self.max_size = (1920, 1080)
        self.quality = 85
        
    async def process_upload(self, upload_file: UploadFile) -> Dict[str, Any]:
        """Обработка загруженного изображения"""
        try:
            # Валидация типа файла
            if not upload_file.content_type.startswith('image/'):
                raise HTTPException(400, "Файл должен быть изображением")
            
            # Создание временного файла
            temp_path = Path(f"/tmp/{upload_file.filename}")
            async with aiofiles.open(temp_path, 'wb') as f:
                content = await upload_file.read()
                await f.write(content)
            
            # Обработка изображения
            processed_info = await self._process_image(temp_path, upload_file.filename)
            
            # Очистка временного файла
            temp_path.unlink()
            
            return {
                "status": "success",
                "original_name": upload_file.filename,
                "processed_url": processed_info["url"],
                "size": processed_info["size"],
                "format": processed_info["format"],
                "file_size": processed_info["file_size"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "original_name": upload_file.filename
            }
    
    async def _process_image(self, image_path: Path, original_name: str) -> Dict[str, Any]:
        """Основная обработка изображения"""
        with Image.open(image_path) as img:
            # Конвертация в RGB если нужно
            if img.mode in ('RGBA', 'P', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Изменение размера с сохранением пропорций
            img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Создание оптимизированной версии
            optimized_path = self._get_optimized_path(original_name)
            img.save(optimized_path, 'JPEG', quality=self.quality, optimize=True)
            
            # Получение информации о файле
            file_size = optimized_path.stat().st_size
            
            return {
                "url": f"/static/uploads/{optimized_path.name}",
                "size": img.size,
                "format": "JPEG",
                "file_size": file_size
            }
    
    def _get_optimized_path(self, original_name: str) -> Path:
        """Генерация пути для оптимизированного изображения"""
        uploads_dir = Path("static/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        name_hash = str(hash(original_name))[-8:]
        optimized_name = f"opt_{name_hash}_{Path(original_name).stem}.jpg"
        return uploads_dir / optimized_name

# Глобальный экземпляр процессора
image_processor = ImageProcessor()