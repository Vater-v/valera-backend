#!/bin/bash

# Остановка при ошибках
set -e

# Проверка .env
if [ ! -f .env ]; then
    echo "Ошибка: файл .env не найден!"
    exit 1
fi

# Экспорт переменных
export $(grep -v '^#' .env | xargs)

# Проверка наличия переменных
if [ -z "$GITHUB_USER" ] || [ -z "$GITHUB_TOKEN" ] || [ -z "$GIT_EMAIL" ] || [ -z "$GIT_NAME" ]; then
    echo "Ошибка: Проверь .env! Не хватает GITHUB_USER, GITHUB_TOKEN, GIT_EMAIL или GIT_NAME."
    exit 1
fi

echo "--- Начинаем синхронизацию ---"

# --- Настройка Git (локально для этого репо) ---
git config user.email "$GIT_EMAIL"
git config user.name "$GIT_NAME"

# 1. Добавляем файлы
git add .

# 2. Делаем коммит
COMMIT_MSG="${1:-Auto-update: $(date '+%Y-%m-%d %H:%M:%S')}"
# Проверка: есть ли что коммитить?
if git diff-index --quiet HEAD --; then
    echo "Нет изменений для коммита."
else
    git commit -m "$COMMIT_MSG"
fi

# 3. Пушим
echo "Заливаем на GitHub..."
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@${REPO_URL}"

echo "--- Успешно! ---"
