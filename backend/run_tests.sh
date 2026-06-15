#!/bin/bash
# MediaPilot 后端测试运行脚本

echo "=========================================="
echo "  MediaPilot Backend Tests"
echo "=========================================="

# 运行单元测试
echo ""
echo "[1/2] Running unit tests..."
pytest tests/unit/ -v --tb=short
UNIT_EXIT_CODE=$?

# 运行集成测试
echo ""
echo "[2/2] Running integration tests..."
pytest tests/integration/ -v --tb=short
INTEGRATION_EXIT_CODE=$?

# 生成覆盖率报告
echo ""
echo "[Coverage] Generating coverage report..."
pytest tests/ --cov=. --cov-report=html --cov-report=term --tb=no

# 总结
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="

if [ $UNIT_EXIT_CODE -eq 0 ] && [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed!"
    exit 1
fi
