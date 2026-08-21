#!/usr/bin/env bash
# 一键初始化:启动服务、跑迁移、建超管、生成示例数据
set -e

cd "$(dirname "$0")"

echo "==> 启动 PostgreSQL"
docker compose up -d db
sleep 5

echo "==> 后端依赖安装"
pip install -r backend/requirements.txt

echo "==> 跑迁移"
python backend/manage.py migrate

echo "==> 创建超级用户 admin/admin"
python backend/manage.py shell < backend/initadmin.py

echo "==> 启动后端 (8000)"
python backend/manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

echo "==> 启动前端 (5173)"
cd frontend
[ -d node_modules ] || npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ 后端: http://127.0.0.1:8000/api/docs  (admin / admin)"
echo "✓ 前端: http://127.0.0.1:5173           (admin / admin)"
echo ""
echo "按 Ctrl+C 停止"
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
