#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_DIR="/opt/fedora-website-generator"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
CURRENT_USER=${SUDO_USER:-$USER}
PYTHON_BIN=${PYTHON_BIN:-python3.11}
VENV_DIR="$BACKEND_DIR/venv"

echo "🔧 Настройка проекта Fedora AI Website Generator"
echo "📁 Проект: $PROJECT_DIR"
echo "👤 Пользователь: $CURRENT_USER"
echo "🐍 Python: $PYTHON_BIN"

# Проверка существования Python
if ! command -v "$PYTHON_BIN" &> /dev/null; then
    echo "❌ Python $PYTHON_BIN не найден!"
    echo "Установите: sudo dnf install python3.11"
    exit 1
fi

# 1) Создание структуры директорий
echo "📁 Создание структуры директорий..."
mkdir -p "$BACKEND_DIR" "$FRONTEND_DIR" "$PROJECT_DIR"/{logs,uploads,generated,cache,static}

# 2) Копирование из исходного репозитория (если существует)
SOURCE_DIR="/home/alex886/Документы/GitHub/fedora-website-generator"
if [ -d "$SOURCE_DIR" ]; then
    echo "📋 Копирование файлов из исходного репозитория..."
    cp -r "$SOURCE_DIR"/backend/* "$BACKEND_DIR"/ 2>/dev/null || echo "ℹ️ Нет файлов в backend для копирования"
    cp -r "$SOURCE_DIR"/frontend/* "$FRONTEND_DIR"/ 2>/dev/null || echo "ℹ️ Нет файлов в frontend для копирования"
    cp -r "$SOURCE_DIR"/configuration/* "$PROJECT_DIR"/ 2>/dev/null || echo "ℹ️ Нет файлов в configuration для копирования"
fi

# 2) Проверка наличия файлов; если отсутствуют — создаём минимальные заглушки
# backend/requirements.txt
if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
  echo "[info] backend/requirements.txt не найден — создаю минимальный requirements.txt"
  cat > "$BACKEND_DIR/requirements.txt" <<'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
openai==1.3.0
python-dotenv==1.0.0
pillow==10.1.0
aiofiles==23.2.1
jinja2==3.1.2
redis==5.0.1
psutil==5.9.6
EOF
fi

# frontend/package.json
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
  echo "[info] frontend/package.json не найден — создаю минимальный package.json"
  mkdir -p "$FRONTEND_DIR"
  cat > "$FRONTEND_DIR/package.json" <<'EOF'
{
  "name": "fedora-site-gen-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}
EOF

  # simple index.html so build has something
  cat > "$FRONTEND_DIR/index.html" <<'EOF'
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Fedora AI Website Generator - Frontend Stub</title>
  </head>
  <body>
    <div id="root">
      <h1>Fedora AI Website Generator — frontend заглушка</h1>
      <p>Если у вас есть реальный фронтенд — замените /opt/fedora-website-generator/frontend содержимым репозитория.</p>
    </div>
    <script>
      console.log("Frontend stub");
    </script>
  </body>
</html>
EOF
fi

# .env.example
if [ ! -f "$PROJECT_DIR/.env.example" ]; then
  echo "[info] .env.example не найден — создаю минимальный .env.example"
  cat > "$PROJECT_DIR/.env.example" <<'EOF'
OPENAI_API_KEY=your_openai_api_key_here
API_KEY=your_internal_api_key
HOST=http://localhost:8000
REDIS_HOST=localhost
REDIS_PORT=6379
MAX_UPLOAD_MB=10
EOF
fi

# backend/systemd unit: если нет — создаём минимальную
if [ ! -f "$BACKEND_DIR/systemd/fedora-website-generator.service" ]; then
  echo "[info] backend/systemd/fedora-website-generator.service не найден — создаю заглушку (можно отредактировать)"
  mkdir -p "$BACKEND_DIR/systemd"
  cat > "$BACKEND_DIR/systemd/fedora-website-generator.service" <<EOF
[Unit]
Description=Fedora AI Website Generator
After=network.target redis.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

# 3) Создание виртуного окружения в backend/venv
echo "🐍 Создаю виртуальное окружение в: $VENV_DIR (если ещё не существует)"
if [ ! -d "$VENV_DIR" ]; then
  $PYTHON_BIN -m venv "$VENV_DIR"
fi

# Активируем venv в текущем процессе (работает в sh/bash)
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 4) Установка Python-зависимостей
echo "📦 Устанавливаю Python зависимости из $BACKEND_DIR/requirements.txt"
pip install --upgrade pip setuptools wheel
pip install -r "$BACKEND_DIR/requirements.txt" || {
  echo "[warn] pip install вернул ошибку. Проверьте вывод выше."
}

# 5) Настройка фронтенда: npm install & build (если установлен npm)
if command -v npm >/dev/null 2>&1; then
  echo "📦 Устанавливаю frontend зависимости и собираю (если есть package.json)"
  pushd "$FRONTEND_DIR" >/dev/null
  if [ -f package.json ]; then
    npm install --no-audit --no-fund || echo "[warn] npm install вернул ошибку — проверьте лог"
    # Build only if vite exists in package.json devDeps/dev scripts
    if grep -q "\"build\"" package.json 2>/dev/null; then
      npm run build || echo "[warn] npm run build вернул ошибку — проверьте фронтенд"
    fi
  else
    echo "[info] Файл package.json не найден в frontend — пропускаю npm install"
  fi
  popd >/dev/null
else
  echo "[warn] npm не установлен — пропущена сборка фронтенда (установите nodejs & npm если нужно)"
fi

# 6) Копирование .env.example -> .env (если .env не существует)
if [ ! -f "$PROJECT_DIR/.env" ]; then
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  echo "[info] .env создан из .env.example — не забудьте отредактировать OPENAI_API_KEY"
else
  echo "[info] .env уже существует — пропускаю копирование"
fi

echo "🔐 Проверьте и отредактируйте .env: nano $PROJECT_DIR/.env"

# 7) Копирование systemd unit (требуется sudo)
if [ -f "$BACKEND_DIR/systemd/fedora-website-generator.service" ]; then
  echo "⚙️ Копирую systemd unit в /etc/systemd/system/ (потребуется sudo)"
  sudo cp "$BACKEND_DIR/systemd/fedora-website-generator.service" /etc/systemd/system/ || {
    echo "[warn] Не удалось скопировать systemd unit — проверьте права"
  }
  sudo systemctl daemon-reload || echo "[warn] systemctl daemon-reload вернул ошибку"
  echo "[info] systemd unit установлен (проверьте и при необходимости редактируйте /etc/systemd/system/fedora-website-generator.service)"
else
  echo "[info] systemd unit не найден в $BACKEND_DIR/systemd — пропущено"
fi

# 8) Правильный владелец файлов — текущий пользователь (не делаем www-data по-умолчанию)
echo "🔧 Устанавливаю владельца файлов на $CURRENT_USER:$CURRENT_USER"
sudo chown -R "$CURRENT_USER":"$CURRENT_USER" "$PROJECT_DIR" || echo "[warn] chown не сработал (возможно, вы уже root)"

echo "✅ Настройка завершена!"
echo "Следующие шаги:"
echo " 1) Отредактируйте $PROJECT_DIR/.env и заполните OPENAI_API_KEY"
echo " 2) (Опционально) Проверьте и замените заглушки backend и frontend на реальные файлы"
echo " 3) Запустите бэкенд вручную для теста:"
echo "    source $VENV_DIR/bin/activate"
echo "    cd $BACKEND_DIR"
echo "    uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo " 4) Если хотите systemd: sudo systemctl enable --now fedora-website-generator"
