# fedora-ai-website-generator
 fedora-ai-website-generator
 
 fedora-ai-website-generator/
├── 🐍 backend/
│   ├── main.py
│   ├── website_agent.py
│   ├── image_processor.py
│   ├── requirements.txt
│   ├── systemd/
│   │   └── fedora-website-generator.service
│   └── nginx/
│       └── fedora-generator.conf
├── ⚛️ frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── DeviceSelector.tsx
│       │   ├── ImageUpload.tsx
│       │   └── PreviewPanel.tsx
│       └── types/
│           └── index.ts
├── 🔧 configuration/
│   ├── install_dependencies.sh
│   ├── .env.example
│   └── setup_project.sh
└── 📚 documentation/
    ├── README.md
    └── API_REFERENCE.md
    
    🚀 ИНСТРУКЦИЯ ПО ЗАПУСКУ НА FEDORA 42
    
Шаг 1: Подготовка системы
# Использовать Python 3.11 в проектах, создавайте виртуальные окружения:
```bash
python3.11 -m venv venv
source venv/bin/activate
sudo dnf install python3-pip python3-virtualenv
pip install --upgrade pip

```bash
# Сделайте скрипты исполняемыми
cd configuration 

chmod +x install_dependencies.sh
chmod +x setup_project.sh

# Установите системные зависимости
./install_dependencies.sh

Шаг 2: Настройка проекта

# Копирование конфигурации
cp .env.example .env

# Редактирование .env файла
nano .env

sudo cp ./setup_project.sh /opt/fedora-website-generator/


# Перейдите в директорию проекта
cd /opt/fedora-website-generator

# Запустите настройку проекта
./setup_project.sh

Шаг 3: Конфигурация переменных окружения


# Укажите ваш OpenAI API ключ и другие настройки:
OPENAI_API_KEY=sk-your-actual-key-here

Шаг 4: Запуск сервисов

# Активация Python окружения
source venv/bin/activate

# Запуск Redis
sudo systemctl start redis
sudo systemctl enable redis

# Запуск бэкенда через systemd
sudo systemctl start fedora-website-generator
sudo systemctl enable fedora-website-generator

# Или ручной запуск для разработки
cd backend
python main.py

Шаг 5: Запуск фронтенда (опционально для разработки)

cd frontend
npm run dev

Шаг 6: Проверка работы

# Проверка статуса сервиса
sudo systemctl status fedora-website-generator

# Проверка через браузер
firefox http://localhost:8000

# Проверка API
curl http://localhost:8000/api/health

Шаг 7: Настройка nginx (опционально для продакшена)

# Копирование конфигурации nginx
sudo cp backend/nginx/fedora-generator.conf /etc/nginx/conf.d/

# Проверка конфигурации
sudo nginx -t

# Перезагрузка nginx
sudo systemctl reload nginx

🎯 КОМАНДЫ УПРАВЛЕНИЯ

# Запуск сервиса
sudo systemctl start fedora-website-generator

# Остановка сервиса  
sudo systemctl stop fedora-website-generator

# Перезапуск сервиса
sudo systemctl restart fedora-website-generator

# Просмотр логов
sudo journalctl -u fedora-website-generator -f

# Проверка статуса
sudo systemctl status fedora-website-generator


🔧 РЕШЕНИЕ ПРОБЛЕМ
Если Redis не запускается:

sudo systemctl status redis
sudo journalctl -u redis -f

Если порт занят:

# Поиск процесса использующего порт
sudo lsof -i :8000

# Или изменение порта в .env файле

Если нет доступа к OpenAI API:

# Проверка API ключа
echo $OPENAI_API_KEY

# Тестирование подключения
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
