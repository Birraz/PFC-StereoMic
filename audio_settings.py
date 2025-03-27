from shared_locks import get_lock


class AudioSettings:


    def __init__(self):
        self._lock = get_lock("audio")  # Get the file lock

        self._eq_bands = {
            1: (60, 5, 1.0),  # Band 1: (frequency, gain, Q-factor)
            2: (250, 3, 1.0),  # Band 2: (frequency, gain, Q-factor)
            3: (1000, 0, 1.0),  # Band 3: (frequency, gain, Q-factor)
            4: (4000, -2, 1.0),  # Band 4: (frequency, gain, Q-factor)
            5: (8000, -1, 1.0)  # Band 5: (frequency, gain, Q-factor)
        }

    # Equalization Accessors
    @property
    def eq_bands(self):
        with self._lock:
            return self._eq_bands

    @eq_bands.setter
    def eq_bands(self, bands):
        """Set all equalizer bands at once."""
        with self._lock:
            if isinstance(bands, dict):
                self._eq_bands = bands
            else:
                raise ValueError("Bands must be a dictionary {band_id: (freq, gain)}")

    def add_eq_band(self, band_id, freq, gain, q=1.0):
        """Add or update a single EQ band."""
        with self._lock:
            self._eq_bands[band_id] = (freq, gain, q)

    def remove_eq_band(self, band_id):
        """Remove a single EQ band."""
        with self._lock:
            if band_id in self._eq_bands:
                del self._eq_bands[band_id]

    def clear_eq_bands(self):
        """Clear all EQ bands."""
        with self._lock:
            self._eq_bands.clear()


# Global instance of AudioSettings (Singleton)
audio_set: AudioSettings = AudioSettings()