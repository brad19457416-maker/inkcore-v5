#!/bin/bash
# 间客全本技法提取 - 后台执行脚本

SCRIPT_DIR="/root/.openclaw/workspace/inkcore-v5"
LOG_FILE="$SCRIPT_DIR/extraction.log"

# 总章节数
TOTAL=1083
BATCH_SIZE=50

# 计算总批次数
BATCHES=$(( (TOTAL + BATCH_SIZE - 1) / BATCH_SIZE ))

echo "========================================" | tee -a "$LOG_FILE"
echo "间客全本技法提取 - 后台执行" | tee -a "$LOG_FILE"
echo "总章节: $TOTAL" | tee -a "$LOG_FILE"
echo "批次大小: $BATCH_SIZE" | tee -a "$LOG_FILE"
echo "总批次数: $BATCHES" | tee -a "$LOG_FILE"
echo "开始时间: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 从第4批开始（前3批已手动完成）
for batch_num in $(seq 4 $BATCHES); do
    START=$(( (batch_num - 1) * BATCH_SIZE + 1 ))
    
    echo "" | tee -a "$LOG_FILE"
    echo "[$batch_num/$BATCHES] 处理第 $START 章开始的 $BATCH_SIZE 章..." | tee -a "$LOG_FILE"
    
    cd "$SCRIPT_DIR" && python3 extract_techniques.py 间客 $START $BATCH_SIZE >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✓ 批次 $batch_num 完成" | tee -a "$LOG_FILE"
    else
        echo "✗ 批次 $batch_num 失败" | tee -a "$LOG_FILE"
    fi
    
    # 每10批暂停1秒，避免系统过载
    if [ $((batch_num % 10)) -eq 0 ]; then
        echo "[$batch_num/$BATCHES] 进度: $((batch_num * 100 / BATCHES))%" | tee -a "$LOG_FILE"
        sleep 1
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "提取完成！" | tee -a "$LOG_FILE"
echo "结束时间: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
