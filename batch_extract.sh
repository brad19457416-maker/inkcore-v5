#!/bin/bash
# 墨芯 v5.0 - 批量技法提取脚本
# 用法: ./batch_extract.sh [小说名] [每批数量]

NOVEL_NAME="${1:-间客}"
BATCH_SIZE="${2:-50}"
SCRIPT_DIR="/root/.openclaw/workspace/inkcore-v5"

echo "========================================"
echo "墨芯 v5.0 - 批量技法提取"
echo "小说: 《$NOVEL_NAME》"
echo "每批: $BATCH_SIZE 章"
echo "========================================"

# 获取已处理章节数
get_processed_count() {
    ls "$SCRIPT_DIR/novels/$NOVEL_NAME/techniques/"*.json 2>/dev/null | wc -l
}

# 获取总章节数
get_total_count() {
    ls "$SCRIPT_DIR/novels/$NOVEL_NAME/chapters/"ch_*.txt 2>/dev/null | wc -l
}

TOTAL=$(get_total_count)
PROCESSED=$(get_processed_count)
REMAINING=$((TOTAL - PROCESSED))

echo ""
echo "总章节: $TOTAL"
echo "已处理: $PROCESSED"
echo "待处理: $REMAINING"
echo ""

if [ $REMAINING -eq 0 ]; then
    echo "✓ 所有章节已处理完毕！"
    exit 0
fi

# 计算批次数
BATCHES=$(( (REMAINING + BATCH_SIZE - 1) / BATCH_SIZE ))
echo "预计批次数: $BATCHES"
echo ""

# 逐批处理
START_FROM=$((PROCESSED + 1))
BATCH_NUM=1

while [ $START_FROM -le $TOTAL ]; do
    echo "----------------------------------------"
    echo "批次 $BATCH_NUM/$BATCHES: 从第 $START_FROM 章开始"
    echo "----------------------------------------"
    
    cd "$SCRIPT_DIR" && python3 extract_techniques.py "$NOVEL_NAME" $START_FROM $BATCH_SIZE
    
    if [ $? -ne 0 ]; then
        echo "✗ 批次 $BATCH_NUM 处理失败"
        exit 1
    fi
    
    PROCESSED=$(get_processed_count)
    START_FROM=$((PROCESSED + 1))
    BATCH_NUM=$((BATCH_NUM + 1))
    
    echo ""
    echo "已完成: $PROCESSED/$TOTAL ($(($PROCESSED * 100 / TOTAL))%)"
    echo ""
done

echo "========================================"
echo "✓ 批量处理完成！"
echo "========================================"
