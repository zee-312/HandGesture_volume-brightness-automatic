"""
main.py — Kontrol Volume & Brightness dengan Gesture Tangan
============================================================
Pakai webcam + MediaPipe untuk deteksi tangan, lalu ukur jarak
jempol-telunjuk untuk mengontrol volume atau brightness.

Kontrol:
  - Geser jempol & telunjuk → atur volume/brightness
  - Tekan 'b' → switch ke mode kontrol brightness layar
  - Tekan 'v' → switch ke mode volume
  - Tekan 'q' → keluar
"""

import os
import sys
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarksConnections,
    RunningMode,
    drawing_utils,
)
from volume_controller import (
    init_volume, set_volume, get_volume,
    set_brightness, get_brightness,
)

# ─── Konfigurasi ─────────────────────────────────────────────
# Jarak jari (dalam pixel) yang dipakai untuk mapping ke 0-100%
# Kalau tangan dekat webcam, jarak pixel besar → naikkan DIST_MAX
# Kalau tangan jauh, jarak pixel kecil → turunkan DIST_MIN
DIST_MIN = 30    # jarak pixel = 0%
DIST_MAX = 250   # jarak pixel = 100%

# Warna (format BGR untuk OpenCV)
COLOR_LINE = (0, 255, 255)     # kuning — garis jempol-telunjuk
COLOR_CIRCLE = (255, 0, 128)   # ungu — titik ujung jari
COLOR_BAR_BG = (50, 50, 50)    # abu gelap — background bar
COLOR_BAR_VOL = (0, 200, 0)    # hijau — bar volume
COLOR_BAR_BRI = (255, 180, 0)  # biru muda — bar brightness
COLOR_TEXT = (255, 255, 255)    # putih — teks

# Path ke file model MediaPipe (harus didownload dulu, lihat README)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "hand_landmarker.task")


def calc_distance(p1, p2):
    """
    Hitung jarak Euclidean antara dua titik.
    Rumus: sqrt((x2-x1)^2 + (y2-y1)^2)
    """
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def map_range(value, in_min, in_max, out_min, out_max):
    """
    Map `value` dari rentang [in_min, in_max] ke [out_min, out_max].
    Sama kayak fungsi map() di Arduino.
    Pakai np.clip supaya hasil tidak keluar dari out_min/out_max.
    """
    mapped = np.interp(value, [in_min, in_max], [out_min, out_max])
    return np.clip(mapped, out_min, out_max)


def draw_bar(frame, percent, mode, x=40, y_top=150, y_bot=400, width=30):
    """
    Gambar progress bar vertikal di frame.
    percent: 0-100
    mode: "volume" atau "brightness" (buat warna & label)
    """
    bar_color = COLOR_BAR_VOL if mode == "volume" else COLOR_BAR_BRI
    bar_height = y_bot - y_top

    # Background bar (kotak abu)
    cv2.rectangle(frame, (x, y_top), (x + width, y_bot), COLOR_BAR_BG, -1)
    # Border
    cv2.rectangle(frame, (x, y_top), (x + width, y_bot), (200, 200, 200), 2)

    # Fill bar dari bawah ke atas sesuai persen
    fill_y = int(y_bot - (percent / 100) * bar_height)
    cv2.rectangle(frame, (x, fill_y), (x + width, y_bot), bar_color, -1)

    # Label teks di atas bar
    label = f"{mode.upper()}: {int(percent)}%"
    cv2.putText(frame, label, (x - 5, y_top - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXT, 2)


def draw_hand_info(frame, thumb_pos, index_pos, distance, percent):
    """Gambar garis, titik, dan info jarak di antara jempol & telunjuk."""
    # Garis penghubung jempol ↔ telunjuk
    cv2.line(frame, thumb_pos, index_pos, COLOR_LINE, 3)

    # Lingkaran di ujung jempol dan telunjuk
    cv2.circle(frame, thumb_pos, 10, COLOR_CIRCLE, -1)
    cv2.circle(frame, index_pos, 10, COLOR_CIRCLE, -1)

    # Titik tengah + teks persen
    mid_x = (thumb_pos[0] + index_pos[0]) // 2
    mid_y = (thumb_pos[1] + index_pos[1]) // 2
    cv2.circle(frame, (mid_x, mid_y), 5, (255, 255, 255), -1)
    cv2.putText(frame, f"{int(percent)}%", (mid_x + 10, mid_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_TEXT, 2)


def draw_mode_label(frame, mode, is_fixed):
    """Tampilkan mode aktif dan petunjuk keyboard di pojok kanan atas."""
    h, w = frame.shape[:2]
    label = f"Mode: {mode.upper()}"
    cv2.putText(frame, label, (w - 250, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_TEXT, 2)
    fix_label = "FIX: ON" if is_fixed else "FIX: OFF"
    cv2.putText(frame, f"{fix_label}  |  '0'=Toggle  'q'=Quit", (w - 390, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def draw_landmarks_on_frame(frame, landmarks):
    """
    Gambar 21 landmark tangan + garis penghubung di frame.
    Pakai drawing_utils bawaan MediaPipe Tasks.
    """
    drawing_utils.draw_landmarks(
        frame,
        landmarks,
        HandLandmarksConnections.HAND_CONNECTIONS,
        drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=3),
        drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2),
    )


def download_model():
    """Download model hand_landmarker.task kalau belum ada."""
    if os.path.exists(MODEL_PATH):
        return
    url = ("https://storage.googleapis.com/mediapipe-models/"
           "hand_landmarker/hand_landmarker/float16/latest/"
           "hand_landmarker.task")
    print(f"[INFO] Downloading model dari {url} ...")
    import urllib.request
    urllib.request.urlretrieve(url, MODEL_PATH)
    print(f"[OK] Model disimpan di {MODEL_PATH}")


def main():
    # --- 0. Download model kalau belum ada ---
    download_model()

    # --- 1. Setup MediaPipe HandLandmarker (Task API baru) ---
    # Kenapa MediaPipe? Karena library ini bisa mendeteksi 21 landmark tangan
    # secara real-time tanpa perlu training model sendiri — tinggal pakai.
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.VIDEO,   # mode video (bukan gambar statis)
        num_hands=1,                      # cukup deteksi 1 tangan
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )
    landmarker = HandLandmarker.create_from_options(options)
    print("[OK] MediaPipe HandLandmarker berhasil diinisialisasi")

    # --- 2. Setup volume (Windows) ---
    try:
        vol_interface, vol_min, vol_max = init_volume()
        current_percent = get_volume(vol_interface, vol_min, vol_max)
        print("[OK] Volume controller berhasil diinisialisasi")
    except Exception as e:
        print(f"[WARNING] Gagal init volume: {e}")
        print("  → Volume control tidak tersedia (bukan Windows?)")
        vol_interface = None
        current_percent = 50

    # --- 3. Buka webcam ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Tidak bisa membuka webcam!")
        landmarker.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print("[OK] Webcam terbuka. Tekan 'q' untuk keluar.")

    mode = "volume"  # mode awal: kontrol volume
    frame_count = 0  # counter untuk timestamp MediaPipe
    is_fixed = False

    # --- 4. Loop utama ---
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Gagal membaca frame dari webcam")
            break

        # Flip horizontal supaya kayak cermin (lebih natural)
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert BGR → RGB karena MediaPipe butuh format RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Buat objek mp.Image dari numpy array, lalu proses
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        # Timestamp naik terus (dalam milidetik) — MediaPipe butuh ini
        # untuk tracking antar-frame di mode VIDEO
        frame_count += 1
        timestamp_ms = int(frame_count * (1000 / 30))  # asumsi ~30 FPS

        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                # Gambar semua landmark tangan (21 titik + garis)
                draw_landmarks_on_frame(frame, hand_landmarks)

                # Ambil posisi ujung jempol (landmark 4) dan telunjuk (landmark 8)
                # Koordinat MediaPipe itu normalized (0-1), jadi kali dengan w dan h
                thumb_tip = hand_landmarks[4]
                index_tip = hand_landmarks[8]

                thumb_pos = (int(thumb_tip.x * w), int(thumb_tip.y * h))
                index_pos = (int(index_tip.x * w), int(index_tip.y * h))

                # Hitung jarak pixel antara jempol dan telunjuk
                distance = calc_distance(thumb_pos, index_pos)

                # Map jarak ke persen (0-100%)
                percent = map_range(distance, DIST_MIN, DIST_MAX, 0, 100)
                # Gesture hanya mengubah controller saat status fix nonaktif.
                if not is_fixed:
                    current_percent = percent
                    if mode == "volume" and vol_interface:
                        set_volume(vol_interface, vol_min, vol_max, percent)
                    elif mode == "brightness":
                        set_brightness(percent)

                # Gambar info visual di frame
                draw_hand_info(frame, thumb_pos, index_pos, distance, percent)

        # Gambar bar dan label mode (selalu tampil, meski tangan tidak terdeteksi)
        if not is_fixed and mode == "volume" and vol_interface:
            current_percent = get_volume(vol_interface, vol_min, vol_max)
        elif not is_fixed and mode == "brightness":
            try:
                current_percent = get_brightness()
            except Exception:
                pass

        draw_bar(frame, current_percent, mode)
        draw_mode_label(frame, mode, is_fixed)

        # Tampilkan frame
        cv2.imshow("Hand Gesture Control", frame)

        # --- 5. Handle keyboard input ---
        key = cv2.waitKeyEx(1) & 0xFFFF
        if key == ord('q'):
            print("Keluar...")
            break
        elif key in (ord('0'), 96):
            is_fixed = not is_fixed
            status = "aktif (nilai dikunci)" if is_fixed else "nonaktif"
            print(f"FIX controller: {status}")
        elif key == ord('v'):
            mode = "volume"
            print("Mode: VOLUME")
        elif key == ord('b'):
            mode = "brightness"
            print("Mode: BRIGHTNESS")

    # --- 6. Cleanup ---
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("Selesai. Webcam dan window ditutup.")


if __name__ == "__main__":
    main()
