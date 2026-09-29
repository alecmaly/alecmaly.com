#!/bin/bash
LOG=/var/log/cpu_monitor.log
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "=== $TIMESTAMP ===" >> $LOG

# Load and CPU
LOAD=$(cat /proc/loadavg)
echo "Load: $LOAD" >> $LOG
top -bn1 | grep "Cpu(s)" >> $LOG

# Memory and swap
free -m | grep -E "Mem|Swap" >> $LOG

# IO wait and disk
iostat -c 1 1 2>/dev/null | tail -1 >> $LOG
df -h / | tail -1 >> $LOG

# Top 10 processes by CPU
echo "-- Top processes (CPU) --" >> $LOG
ps aux --sort=-%cpu | head -11 >> $LOG

# Top 5 by memory
echo "-- Top processes (MEM) --" >> $LOG
ps aux --sort=-%mem | head -6 >> $LOG

# Process count
echo "Processes: $(ps aux | wc -l)" >> $LOG

# Network connections summary
echo "Connections: $(ss -s 2>/dev/null | grep estab | head -1)" >> $LOG

# Docker stats
echo "-- Docker --" >> $LOG
docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" >> $LOG 2>&1

echo "" >> $LOG

# Keep last 100000 lines (~3-4 days)
tail -100000 $LOG > ${LOG}.tmp && mv ${LOG}.tmp $LOG
