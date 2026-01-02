#!/bin/bash

# Читаем .env
if [ ! -f .env ]; then
    echo "Ошибка: файл .env не найден!"
    exit 1
fi
export $(grep -v '^#' .env | xargs)

echo "--- Начинаем синхронизацию ---"

# Настройка (чтобы не ругался на email/name каждый раз)
git config user.email "$GIT_EMAIL"
git config user.name "$GIT_NAME"

# 1. Добавляем файлы
git add .

# 2. Коммит
# "|| true" означает: если коммитить нечего (уже закоммитил), не падай, иди дальше к пушу
COMMIT_MSG="${1:-Auto-update: $(date '+%Y-%m-%d %H:%M:%S')}"
git commit -m "$COMMIT_MSG" || true

# 3. Пушим в ветку master
echo "Заливаем на GitHub..."
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@${REPO_URL}" master

echo "--- Готово! ---"
