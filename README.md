# LZW Compression Project / LZW Sıkıştırma Projesi

[![CI](https://github.com/alirkal34-jpg/xxy/actions/workflows/ci.yml/badge.svg)](https://github.com/alirkal34-jpg/xxy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 🇹🇷 Türkçe

### Proje Özeti
Bu proje, **LZW (Lempel–Ziv–Welch)** algoritmasını kullanarak metin ve görüntü verilerinin sıkıştırılması/açılması için geliştirilmiştir.

- Metin sıkıştırma örnekleri (`LZW.py` tabanlı)
- Görüntü ve metin için çok seviyeli sıkıştırma (`level1`–`level5`)
- PyQt5 tabanlı masaüstü arayüz (`main_gui.py`)

### Özellikler
- Seviye bazlı sıkıştırma yaklaşımı (1–5)
- Metin, gri tonlu ve renkli görüntü desteği
- `.lzw` formatında ikili çıktı kaydı/yükleme
- Sıkıştırma ölçümleri ve kalite metrikleri:
  - Entropi (Entropy)
  - CR/CF/SS (Compression Ratio / Compression Factor / Space Saving)
  - PSNR/MSE (görüntü kalite ölçümleri)

### Gereksinimler
- Python **3.10+**
- `PyQt5`
- `numpy`
- `opencv-python`

### Kurulum
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### Kullanım
#### GUI çalıştırma
```bash
python main_gui.py
```

#### Metin örnekleri
```bash
python text_file_compression_example.py
python text_file_decompression_example.py
```

### Seviye Açıklamaları (1–5)
- **Level 1 - Text**: Ham metin üzerinde klasik LZW.
- **Level 2 - Grayscale**: Gri tonlu görüntü piksel akışı üzerinde LZW.
- **Level 3 - Grayscale Diff**: Gri tonlu görüntüde fark (difference) + LZW.
- **Level 4 - Color**: Renk kanallarına dayalı LZW sıkıştırma.
- **Level 5 - Color Diff**: Renk fark temelli yaklaşım + LZW.

### `.lzw` Dosya Formatı Notları
GUI tarafında `.lzw` dosyası; sabit boyutlu başlık + değişken uzunluklu sıkıştırılmış bit akışını içerir. Başlıkta seviye, kod uzunluğu ve ilgili boyut/segment bilgileri tutulur; böylece açma işlemi dosya içeriğinden tekrar üretilebilir.

### Metriklerin Kısa Anlamı
- **Entropy**: Verinin teorik bilgi yoğunluğu.
- **CR (Compression Ratio)**: Sıkıştırılmış/orijinal boyut oranı (küçük olması iyidir).
- **CF (Compression Factor)**: Orijinal/sıkıştırılmış boyut oranı (büyük olması iyidir).
- **SS (Space Saving)**: Sağlanan alan tasarrufu yüzdesi.
- **MSE**: Orijinal ve geri açılmış görüntü arasındaki ortalama karesel hata.
- **PSNR**: Görüntü kalitesini dB cinsinden ölçer (yüksek olması iyidir).

### Proje Yapısı
```text
.
├── main_gui.py
├── lzw_utils.py
├── LZW.py
├── level1_text.py
├── level2_grayscale.py
├── level3_compression.py
├── level4_color_compression.py
├── level5_color_diff_compression.py
├── text_file_compression_example.py
├── text_file_decompression_example.py
├── requirements.txt
├── LICENSE
└── .github/workflows/ci.yml
```

### Katkı
Katkı kuralları için `CONTRIBUTING.md` dosyasına bakın.

### Lisans
Bu proje **MIT License** ile lisanslanmıştır. Ayrıntılar için `LICENSE` dosyasına bakın.

---

## 🇬🇧 English

### Overview
This project implements **LZW (Lempel–Ziv–Welch)** compression/decompression for text and image data.

- Text compression examples (`LZW.py` based)
- Multi-level compression pipeline for text/images (`level1`–`level5`)
- PyQt5 desktop GUI (`main_gui.py`)

### Features
- Level-based compression workflow (1–5)
- Text, grayscale, and color image support
- Binary `.lzw` save/load workflow
- Compression and quality metrics:
  - Entropy
  - CR/CF/SS (Compression Ratio / Compression Factor / Space Saving)
  - PSNR/MSE for image quality

### Requirements
- Python **3.10+**
- `PyQt5`
- `numpy`
- `opencv-python`

### Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### Usage
#### Run GUI
```bash
python main_gui.py
```

#### Text examples
```bash
python text_file_compression_example.py
python text_file_decompression_example.py
```

### Levels 1–5 (Brief)
- **Level 1 - Text**: Classic LZW on raw text.
- **Level 2 - Grayscale**: LZW on grayscale pixel stream.
- **Level 3 - Grayscale Diff**: Difference-based grayscale preprocessing + LZW.
- **Level 4 - Color**: Channel-oriented color compression with LZW.
- **Level 5 - Color Diff**: Difference-based color preprocessing + LZW.

### `.lzw` File Notes
In the GUI flow, `.lzw` files contain a fixed-size header and compressed bitstream payload. The header stores level, code-length, and dimensional/segment metadata required for deterministic decompression.

### Metrics Explained
- **Entropy**: Theoretical information density of source data.
- **CR (Compression Ratio)**: Compressed/original size ratio (lower is better).
- **CF (Compression Factor)**: Original/compressed size ratio (higher is better).
- **SS (Space Saving)**: Percentage of saved storage space.
- **MSE**: Mean squared error between original and reconstructed images.
- **PSNR**: Peak signal-to-noise ratio in dB (higher is better).

### Project Structure
See the structure section above (shared tree).

### Contributing
Please read `CONTRIBUTING.md`.

### License
This project is licensed under the **MIT License**. See `LICENSE` for details.
