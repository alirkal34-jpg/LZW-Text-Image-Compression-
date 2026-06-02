# 🗜️ LZW Text & Image Compression

A Python implementation of the **Lempel–Ziv–Welch (LZW)** lossless compression algorithm supporting both text and multi-level image compression, with a full **PyQt5 GUI**.

---

## ✨ Features

- **5 Compression Levels** — from simple text to color image with differential encoding
- **Lossless Compression** — pixel-perfect reconstruction verified with PSNR/MSE metrics
- **Interactive GUI** — load, compress, decompress, and save files with a single click
- **Real-Time Metrics** — Compression Ratio (CR), Compression Factor (CF), Space Savings (SS), Entropy
- **Multithreaded** — compression/decompression runs in background threads (no UI freeze)
- **Progressive LZW** — dynamic code-length growth from 8-bit up to 16-bit

---

## 🗂️ Project Structure

```
├── LZW.py                          # Core LZW encode/decode engine (text)
├── lzw_utils.py                    # Shared utilities: bitstream, padding, header I/O
├── level1_text.py                  # Level 1 — Text compression (LZW on UTF-8)
├── level2_grayscale.py             # Level 2 — Grayscale image compression
├── level3_compression.py           # Level 3 — Grayscale + Differential encoding
├── level4_color_compression.py     # Level 4 — Color image (B/G/R channels)
├── level5_color_diff_compression.py# Level 5 — Color + Differential encoding
├── main_gui.py                     # PyQt5 GUI application (main entry point)
├── text_file_compression_example.py
├── text_file_decompression_example.py
├── sample.txt                      # Sample text file for testing
└── docs/
    ├── Flow Chart.jpg              # LZW algorithm flow chart
    ├── Class Diagram.jpg           # UML class diagram
    └── flowchart.jpg               # Compression pipeline flowchart
```

---

## 🔢 Compression Levels

| Level | Input | Method | Notes |
|-------|-------|--------|-------|
| **1** | `.txt` | LZW on characters | Entropy-based, lossless |
| **2** | `.png` / `.bmp` | LZW on grayscale pixels | Single channel |
| **3** | `.png` / `.bmp` | LZW on grayscale pixel differences | Better compression via differential |
| **4** | `.png` / `.bmp` | LZW on B/G/R channels independently | Full color |
| **5** | `.png` / `.bmp` | LZW on color channel differences | Best compression ratio |

---

## 📊 Metrics Explained

| Metric | Formula | Meaning |
|--------|---------|---------|
| **CR** | `compressed / original` | Compression Ratio (lower = better) |
| **CF** | `original / compressed` | Compression Factor (higher = better) |
| **SS** | `(original - compressed) / original` | Space Savings (%) |
| **Entropy** | Shannon entropy | Theoretical lower bound on compression |
| **PSNR** | `10 × log₁₀(255² / MSE)` | Signal quality (∞ = lossless) |
| **MSE** | Mean Squared Error | Pixel-level reconstruction error |

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install PyQt5 opencv-python numpy
```

### Run the GUI

```bash
python main_gui.py
```

### Run Text Compression Example

```bash
python text_file_compression_example.py
python text_file_decompression_example.py
```

---

## 🖥️ GUI Usage

1. **Load Data** — Select a `.txt`, `.png`, or `.bmp` file
2. **Choose Level** — Pick a compression level (1–5) matching your file type
3. **Compress** — Results and metrics are shown instantly
4. **Save** — Export the compressed `.lzw` binary file
5. **Decompress** — Load a `.lzw` file and reconstruct the original
6. **Save Restored** — Export the decompressed text or image

---

## 🏗️ Architecture

The binary `.lzw` file format:

```
[ 7 × 16-bit Header ] [ Encoded Bit Stream ] [ Padding ]
  level | codelength | height | width | l1 | l2 | l3
```

- **Header** encodes all metadata needed for decompression
- **Progressive encoding** allows the dictionary to grow dynamically
- **Padding** ensures byte-aligned storage

---

## 🧪 Algorithm Overview

```
LZW Compression:
  Initialize dict with 256 ASCII entries
  For each symbol:
    If (current + symbol) in dict → extend current
    Else → output code for current, add new entry, reset
  Output final code

LZW Decompression:
  Initialize dict with 256 ASCII entries
  Read code → look up dict → output → extend dict
  Handle special case: code == dict_size
```

---

## 👤 Author

**Ali Rubar Kal** — Computer Engineering Student  
[GitHub](https://github.com/alirkal34-jpg)

---

## 📄 License

This project was developed as a university assignment. All rights reserved.
