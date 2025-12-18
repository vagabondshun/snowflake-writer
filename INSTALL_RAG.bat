@echo off
echo ========================================
echo Snowflake Writer - RAG 依赖安装脚本
echo ========================================
echo.

REM 检查Python 3.12是否已安装
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python 3.12
    echo.
    echo 请先安装Python 3.12:
    echo https://www.python.org/downloads/release/python-3120/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [✓] 检测到Python 3.12
py -3.12 --version
echo.

REM 创建虚拟环境
echo [1/4] 创建虚拟环境...
if exist venv_rag (
    echo 虚拟环境已存在，跳过创建
) else (
    py -3.12 -m venv venv_rag
    echo [✓] 虚拟环境创建完成
)
echo.

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
call venv_rag\Scripts\activate.bat
echo [✓] 虚拟环境已激活
echo.

REM 升级pip
echo [3/4] 升级pip...
python -m pip install --upgrade pip --quiet
echo [✓] pip已升级
echo.

REM 安装依赖
echo [4/4] 安装RAG依赖（可能需要几分钟）...
pip install chromadb sentence-transformers --quiet
if %errorlevel% neq 0 (
    echo [错误] 安装失败
    pause
    exit /b 1
)
echo [✓] 依赖安装完成
echo.

REM 测试安装
echo ========================================
echo 测试RAG系统...
echo ========================================
python -c "from style_rag import check_dependencies; deps = check_dependencies(); print('✓ chromadb:', '已安装' if deps['chromadb'] else '未安装'); print('✓ sentence-transformers:', '已安装' if deps['sentence_transformers'] else '未安装'); print(); print('✅ RAG系统就绪！' if deps['all_available'] else '❌ 安装失败')"
echo.

REM 运行测试
echo ========================================
echo 运行RAG测试（首次会下载400MB中文模型）...
echo ========================================
python tests\test_style_rag.py
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 使用方法:
echo   1. 每次使用前激活环境: venv_rag\Scripts\activate
echo   2. 运行你的代码: python your_script.py
echo   3. 退出环境: deactivate
echo.
pause
