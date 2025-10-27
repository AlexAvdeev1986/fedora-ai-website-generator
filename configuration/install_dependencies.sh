#!/bin/bash
echo "🚀 Установка Fedora AI Website Generator на Fedora 42"

# Обновление системы
sudo dnf update -y

# Установка Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-virtualenv python3.11-devel

# Установка Node.js 18+
sudo dnf install -y nodejs npm

# Установка системных зависимостей
sudo dnf install -y gcc-c++ make openssl-devel bzip2-devel libffi-devel zlib-devel

# Установка Redis
sudo dnf install -y redis
sudo systemctl enable redis
sudo systemctl start redis

# Установка nginx (опционально)
sudo dnf install -y nginx

# Создание директории проекта
sudo mkdir -p /opt/fedora-website-generator
sudo chown $USER:$USER /opt/fedora-website-generator

echo "✅ Зависимости установлены успешно!"
echo "📁 Проект будет расположен в: /opt/fedora-website-generator"