import wave
import struct
import math
import random

def create_tone(filename, duration, freqs, type="sine", decay=True, noise_level=0.0):
    sample_rate = 44100
    obj = wave.open(filename, 'w')
    obj.setnchannels(1)
    obj.setsampwidth(2)
    obj.setframerate(sample_rate)
    
    num_samples = int(sample_rate * duration)
    for i in range(num_samples):
        t = float(i) / sample_rate
        val = 0
        for f in freqs:
            if type == "sine":
                val += math.sin(2.0 * math.pi * f * t)
            elif type == "square":
                val += 1.0 if math.sin(2.0 * math.pi * f * t) > 0 else -1.0
        val /= len(freqs)
        
        # Add some eerie noise
        if noise_level > 0:
            val += (random.random() * 2 - 1) * noise_level
            
        if decay:
            val *= math.exp(-3 * t / duration)
            
        # Clamp
        val = max(min(val, 1.0), -1.0)
        
        data = struct.pack('<h', int(val * 32767.0))
        obj.writeframesraw(data)
    obj.close()

# Eerie select sound (low heartbeat like thud)
create_tone("D:\\select.wav", 0.2, [60], type="sine", decay=True, noise_level=0.1)

# Eerie win sound (chilling chord)
create_tone("D:\\win.wav", 1.5, [440, 466, 880], type="sine", decay=True, noise_level=0.05)

# Eerie lose sound (low descending rumble - fake it with low freq)
create_tone("D:\\lose.wav", 1.5, [80, 85, 90], type="sine", decay=True, noise_level=0.2)

# Eerie tie sound (flat static)
create_tone("D:\\tie.wav", 1.0, [200], type="sine", decay=True, noise_level=0.4)

print("Sounds generated.")
