# ⚙️ **Оптимизация VTT для разных моделей MacBook**

## 🎯 **Текущие настройки оптимизированы для:**
- **MacBook Pro с M4 Max** (16 ядер, 128GB RAM)

## 📊 **Рекомендации для других моделей:**

### 🏃‍♂️ **MacBook Pro M3 Max / M4 Pro** (12 ядер, 36GB-64GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 8192    # 8GB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 600  # 10 мин вместо 15 мин
    max_chunk_duration_sec: 90 # 1.5 мин вместо 2 мин

# superwhisper.py
max_workers=6  # 6 ядер вместо 8
```

### 💪 **MacBook Pro M3 Pro** (11 ядер, 18GB-36GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 4096    # 4GB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 480  # 8 мин вместо 15 мин
    max_chunk_duration_sec: 60 # 1 мин вместо 2 мин

# superwhisper.py
max_workers=5  # 5 ядер вместо 8
```

### 🚀 **MacBook Pro M3** (8 ядер, 8GB-24GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 2048    # 2GB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 360  # 6 мин вместо 15 мин
    max_chunk_duration_sec: 45 # 45 сек вместо 2 мин

# superwhisper.py
max_workers=4  # 4 ядра вместо 8
```

### 💻 **MacBook Air M2/M3** (8 ядер, 8GB-16GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 1024    # 1GB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 240  # 4 мин вместо 15 мин
    max_chunk_duration_sec: 30 # 30 сек вместо 2 мин

# superwhisper.py
max_workers=3  # 3 ядра вместо 8
```

### 🖥️ **MacBook Air M1** (8 ядер, 8GB-16GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 1024    # 1GB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 180  # 3 мин вместо 15 мин
    max_chunk_duration_sec: 30 # 30 сек вместо 2 мин

# superwhisper.py
max_workers=2  # 2 ядра вместо 8
```

### 📱 **MacBook Air M1 7-core GPU** (7 ядер, 8GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 512     # 512MB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 120  # 2 мин вместо 15 мин
    max_chunk_duration_sec: 25 # 25 сек вместо 2 мин

# superwhisper.py
max_workers=2  # 2 ядра вместо 8
```

### 🖥️ **Mac Mini / iMac M1/M2** (8 ядер, 8GB-32GB RAM)
```yaml
# config.yaml
performance:
  memory_limit_mb: 2048    # 2GB вместо 16GB
  chunk_processing:
    chunk_threshold_sec: 300  # 5 мин вместо 15 мин
    max_chunk_duration_sec: 45 # 45 сек вместо 2 мин

# superwhisper.py
max_workers=4  # 4 ядра вместо 8
```

## 🔧 **Как узнать характеристики своего Mac:**

```bash
# В терминале:
system_profiler SPHardwareDataType | grep -E "(Chip|Total Number|Memory)"

# Или в меню Apple → О программе этом Mac
```

## 📝 **Быстрая настройка:**

1. **Узнай модель своего Mac**
2. **Найди соответствующий раздел выше**
3. **Скопируй настройки в `config.yaml`**
4. **Измени `max_workers` в `superwhisper.py`**
5. **Перезапусти приложение**

## ⚡ **Общие рекомендации:**

- **Больше ядер** = выше `max_workers`
- **Больше RAM** = выше `memory_limit_mb`
- **Для слабых Mac** = меньше `chunk_threshold_sec`
- **Для мощных Mac** = можно увеличить `chunk_overlap_sec` для лучшей точности

## 🚀 **M4 Max настройки (текущие):**
- 16 ядер → `max_workers=8`
- 128GB RAM → `memory_limit_mb=16384`
- 15 мин без чанков
- 2 мин чанки
