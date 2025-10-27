#!/bin/bash
PROJECT_DIR="/opt/fedora-website-generator"

echo "🔧 Настройка проекта Fedora AI Website Generator"

# Создание структуры директорий
mkdir -p $PROJECT_DIR/{backend,frontend,logs,uploads,generated,cache,static}

# Копирование файлов проекта (предполагается, что файлы уже там)
cd $PROJECT_DIR

# Настройка Python виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
pip install -r backend/requirements.txt

# Настройка фронтенда
cd frontend
npm install
npm run build

# Копирование конфигурации
cd $PROJECT_DIR
cp configuration/.env.example .env

echo "📝 Настройте переменные окружения: nano .env"
echo "🔑 Получите OpenAI API ключ: https://platform.openai.com/api-keys"

# Настройка systemd сервиса
sudo cp backend/systemd/fedora-website-generator.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "✅ Настройка завершена!"
echo "🚀 Запуск: sudo systemctl start fedora-website-generator"
echo "📊 Статус: sudo systemctl status fedora-website-generator"
