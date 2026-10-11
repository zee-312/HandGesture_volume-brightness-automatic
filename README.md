# 🖐️ Kontrol Volume & Brightness dengan Gesture Tangan

Aplikasi Python real-time yang mendeteksi tangan lewat webcam dan menggunakan jarak antara ujung jempol & telunjuk untuk mengontrol **volume sistem** atau **brightness layar**.

![Demo](https://img.shields.io/badge/Python-3.8%2B-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-orange)

---

## 📦 Instalasi

### 1. Clone / Download project ini

```
cd hand-gesture-control
```

### 2. (Opsional tapi disarankan) Buat virtual environment

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Catatan Windows:** Library `pycaw` dan `comtypes` hanya berjalan di Windows.
> Di Mac/Linux, kontrol volume tidak tersedia (aplikasi tetap jalan tapi tanpa fitur volume).
> Brightness control (`screen_brightness_control`) bisa jalan di Windows, Mac, dan Linux.

> **Model file:** Saat pertama kali dijalankan, program akan otomatis mendownload
> file model `hand_landmarker.task` (~10 MB) dari Google Storage. Pastikan ada koneksi internet.



## 🚀 Cara Menjalankan

```bash
python main.py
```

### Kontrol Keyboard
| Tombol | Fungsi |
|--------|--------|
| `v`    | Mode **Volume** (default) |
| `b`    | Mode **Brightness** |
| `0`    | Toggle **FIX** controller |
| `q`    | Keluar dari aplikasi |

Tekan `0` untuk mengunci nilai controller. Tekan `0` lagi untuk mengaktifkan
kembali kontrol gesture.

### Cara Pakai
1. Jalankan `python main.py` → webcam akan terbuka
2. Angkat tangan di depan webcam
3. **Dekatkan** jempol & telunjuk → volume/brightness turun (mendekati 0%)
4. **Jauhkan** jempol & telunjuk → volume/brightness naik (mendekati 100%)
5. Tekan `b` untuk switch ke brightness, `v` untuk balik ke volume
6. Tekan `0` jika ingin mempertahankan nilai volume/brightness saat ini
7. Tekan `q` untuk keluar

---

## 📁 Struktur Project

```
hand-gesture-control/
├── main.py                 # Program utama (webcam, deteksi, UI)
├── volume_controller.py    # Helper untuk kontrol volume & brightness
├── hand_landmarker.task    # Model ML MediaPipe (auto-download)
├── requirements.txt        # Daftar library yang dibutuhkan
└── README.md               # File ini
```

---

## ⚙️ Kustomisasi

Di `main.py` ada konfigurasi yang bisa diubah:

```python
DIST_MIN = 30    # jarak pixel saat jari dirapatkan (= 0%)
DIST_MAX = 250   # jarak pixel saat jari direnggangkan (= 100%)
```

Kalau kontrol terasa terlalu sensitif, **naikkan** `DIST_MAX`.
Kalau kurang responsif, **turunkan** `DIST_MIN`.

---

## 🔧 Catatan Platform

| Fitur | Windows | Mac | Linux |
|-------|---------|-----|-------|
| Webcam + Deteksi Tangan | ✅ | ✅ | ✅ |
| Kontrol Volume (pycaw) | ✅ | ❌ | ❌ |
| Kontrol Brightness | ✅ | ✅ | ✅* |

> \*Linux: brightness control butuh akses ke `/sys/class/backlight/`. Mungkin perlu `sudo`.

Untuk Mac/Linux volume control, bisa pakai `osascript` (Mac) atau `pactl` (Linux) sebagai alternatif — tapi belum diimplementasi di project ini.

---

## 📚 Library yang Dipakai

- **OpenCV** (`opencv-python`) — capture webcam & tampilkan video
- **MediaPipe** (`mediapipe`) — deteksi landmark tangan (21 titik)
- **NumPy** (`numpy`) — operasi matematika (jarak, mapping)
- **pycaw** — kontrol volume Windows via Core Audio API
- **screen_brightness_control** — kontrol brightness layar
