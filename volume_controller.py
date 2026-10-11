"""
volume_controller.py
Modul kecil untuk mengontrol volume sistem Windows pakai pycaw,
dan brightness layar pakai screen_brightness_control.
"""

# === VOLUME (Windows only, pakai pycaw) ===

def init_volume():
    """
    Inisialisasi interface volume Windows.
    Return: (volume_interface, vol_min, vol_max)
    
    Kenapa pycaw? Karena pycaw adalah wrapper Python untuk
    Windows Core Audio API — cara paling reliable untuk
    mengubah volume sistem di Windows.
    """
    from pycaw.pycaw import AudioUtilities

    speakers = AudioUtilities.GetSpeakers()
    # pycaw versi baru: langsung akses .EndpointVolume
    volume = speakers.EndpointVolume

    vol_min, vol_max, _ = volume.GetVolumeRange()
    return volume, vol_min, vol_max


def set_volume(volume_interface, vol_min, vol_max, percent):
    """
    Set volume sistem ke nilai `percent` (0-100).
    pycaw pakai skala dB (desibel), jadi kita convert persen ke dB.
    """
    import numpy as np
    # Map 0-100% ke rentang dB (vol_min sampai vol_max)
    db_value = np.interp(percent, [0, 100], [vol_min, vol_max])
    volume_interface.SetMasterVolumeLevel(db_value, None)


def get_volume(volume_interface, vol_min, vol_max):
    """Ambil volume saat ini dalam persen (0-100)."""
    import numpy as np
    current_db = volume_interface.GetMasterVolumeLevel()
    percent = np.interp(current_db, [vol_min, vol_max], [0, 100])
    return percent


# === BRIGHTNESS (cross-platform, pakai screen_brightness_control) ===

def set_brightness(percent):
    """Set brightness layar ke nilai `percent` (0-100)."""
    import screen_brightness_control as sbc
    sbc.set_brightness(int(percent))


def get_brightness():
    """Ambil brightness layar saat ini (0-100)."""
    import screen_brightness_control as sbc
    brightness = sbc.get_brightness()
    # sbc.get_brightness() return list (bisa ada >1 monitor), ambil yang pertama
    if isinstance(brightness, list):
        return brightness[0]
    return brightness
