@echo off
REM Windows 一键启动
setlocal

cd /d "%~dp0"

echo ==^> 启动 PostgreSQL
docker compose up -d db

echo ==^> 后端依赖
pip install -r backend\requirements.txt

echo ==^> 迁移
python backend\manage.py migrate

echo ==^> 创建超管 admin/admin
python backend\manage.py shell ^< backend\initadmin.py

echo ==^> 启动后端 (8000)
start "autotest-backend" cmd /k "cd backend && python manage.py runserver 0.0.0.0:8000"

echo ==^> 启动前端 (5173)
cd frontend
if not exist node_modules npm install
start "autotest-frontend" cmd /k "npm run dev"

echo.
echo Backend: http://127.0.0.1:8000/api/docs  (admin / admin)
echo Frontend: http://127.0.0.1:5173           (admin / admin)
endlocal
