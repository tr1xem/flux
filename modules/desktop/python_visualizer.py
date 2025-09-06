import numpy as np
import sounddevice as sd
import threading
import time
from ignis import widgets
from gi.repository import Gdk, GLib, Gtk
from loguru import logger

# Enhanced Desktop Visualizer Configuration
SAMPLE_RATE = 44100
BLOCK_SIZE = 2048  # Increased for better frequency resolution
CHANNELS = 1
DESKTOP_BARS = 80  # More bars for wider desktop
VISUALIZER_HEIGHT = 300  # Much taller for better visibility
MARGIN = 10  # Reduced margin for more width

# Enhanced Visual settings for upward bars
BAR_MIN_WIDTH = 3   # Thinner bars like in image
BAR_MAX_WIDTH = 8   # Maximum thinner bars  
BAR_SPACING = 4     # More spacing between bars
BAR_ROUNDNESS = 2   # Less rounded for sharper look

# Clean monochrome color scheme like in image
CLEAN_WHITE = "#FFFFFF"
CLEAN_ALPHA = 0.9

def parse_color(hex_color):
    """Convert hex color to RGBA tuple"""
    return (
        int(hex_color[1:3], 16) / 255.0,
        int(hex_color[3:5], 16) / 255.0,
        int(hex_color[5:7], 16) / 255.0,
        CLEAN_ALPHA
    )

# Clean white color for bars
CLEAN_COLOR = parse_color(CLEAN_WHITE)

class PythonAudioProcessor:
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.running = False
        self.stream = None
        self.audio_buffer = np.zeros(BLOCK_SIZE)
        self.window = np.hanning(BLOCK_SIZE)
        
        # Initialize smoothing arrays for smoother animation
        self.previous_bars = np.zeros(DESKTOP_BARS)
        
        # Frequency bins for visualization
        self.freq_bins = np.linspace(0, SAMPLE_RATE // 2, BLOCK_SIZE // 2)
        
        # Create frequency ranges for bars
        self.bar_freqs = self.create_frequency_ranges()
        
        # Debug: Print frequency ranges for dramatic differences
        logger.info("Frequency ranges for dramatic visualization:")
        for i in range(min(15, len(self.bar_freqs))):
            start_f, end_f = self.bar_freqs[i]
            logger.info(f"Bar {i:2d}: {start_f:6.1f}Hz - {end_f:6.1f}Hz")
        
    def create_frequency_ranges(self):
        """Create frequency ranges with most used frequencies in center, least used at ends"""
        
        # Define frequency bands from least used to most used
        # LEAST USED (edges): Very low bass, very high treble
        # MOST USED (center): Vocals, guitars, drums, main musical content
        
        frequency_bands = []
        
        # LEFT SIDE - least used to more used frequencies
        frequency_bands.extend([
            # Very low bass (edges) - least musical content
            (20, 40), (40, 60), (60, 80), (80, 100), (100, 120),
            # Low bass - some kick drums
            (120, 150), (150, 180), (180, 220), (220, 260), (260, 300),
            # Bass fundamentals - bass guitar, low toms
            (300, 350), (350, 400), (400, 450), (450, 500), (500, 600),
            # Lower mids - guitar fundamentals, snare body
            (600, 700), (700, 800), (800, 900), (900, 1000), (1000, 1200),
        ])
        
        # CENTER - most used frequencies (vocals, guitars, main musical content)
        frequency_bands.extend([
            # Vocal fundamentals and guitar presence - MOST IMPORTANT
            (1200, 1400), (1400, 1600), (1600, 1800), (1800, 2000),
            # Core vocal range - MOST MUSICAL CONTENT
            (2000, 2200), (2200, 2400), (2400, 2600), (2600, 2800), 
            (2800, 3000), (3000, 3200), (3200, 3400), (3400, 3600),
            # Vocal clarity and presence - VERY IMPORTANT
            (3600, 3800), (3800, 4000), (4000, 4200), (4200, 4400),
            # Vocal brightness and consonants
            (4400, 4600), (4600, 4800), (4800, 5000), (5000, 5200),
        ])
        
        # RIGHT SIDE - from more used back to least used frequencies  
        frequency_bands.extend([
            # High mids - cymbals, vocal air
            (5200, 5500), (5500, 5800), (5800, 6200), (6200, 6600), (6600, 7000),
            # Highs - brightness, cymbals
            (7000, 7500), (7500, 8000), (8000, 8500), (8500, 9000), (9000, 9500),
            # High treble - air, sparkle
            (9500, 10500), (10500, 11500), (11500, 12500), (12500, 13500), (13500, 14500),
            # Very high treble (edges) - least musical content  
            (14500, 15500), (15500, 16500), (16500, 17500), (17500, 18500), (18500, 20000),
        ])
        
        # Ensure we have exactly 80 bars
        if len(frequency_bands) > DESKTOP_BARS:
            frequency_bands = frequency_bands[:DESKTOP_BARS]
        elif len(frequency_bands) < DESKTOP_BARS:
            # Fill remaining with high frequency bands
            remaining = DESKTOP_BARS - len(frequency_bands)
            for i in range(remaining):
                start_freq = 18500 + (i * 200)
                end_freq = start_freq + 200
                frequency_bands.append((start_freq, min(end_freq, 20000)))
        
        # Debug: Print the center frequencies to show distribution
        logger.info("Frequency distribution (most used in center):")
        for i in range(min(15, len(frequency_bands))):
            start_f, end_f = frequency_bands[i]
            center_f = (start_f + end_f) / 2
            position = "LEFT_EDGE" if i < 5 else "LEFT_SIDE"
            logger.info(f"Bar {i:2d}: {start_f:6.1f}Hz - {end_f:6.1f}Hz (center: {center_f:6.1f}Hz) [{position}]")
        
        # Show center bars
        center_start = len(frequency_bands) // 2 - 5
        center_end = len(frequency_bands) // 2 + 5
        for i in range(center_start, min(center_end, len(frequency_bands))):
            start_f, end_f = frequency_bands[i]
            center_f = (start_f + end_f) / 2
            logger.info(f"Bar {i:2d}: {start_f:6.1f}Hz - {end_f:6.1f}Hz (center: {center_f:6.1f}Hz) [CENTER - MOST USED]")
            
        return frequency_bands
    
    def audio_callback(self, indata, frames, time, status):
        """Real-time audio callback with enhanced processing"""
        if status:
            logger.warning(f"Audio callback status: {status}")
            
        # Convert to mono if needed
        if len(indata.shape) > 1 and indata.shape[1] > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
            
        # Check if we're getting any real audio input
        rms = np.sqrt(np.mean(audio_data**2))
        
        # If audio is very quiet, show minimal bars (not full test pattern)
        if rms < 5e-3:  # Even less sensitive threshold
            # Just show very small baseline bars
            bar_values = np.ones(DESKTOP_BARS) * 0.01  # Even smaller baseline
            GLib.idle_add(self.visualizer.update_visualization, bar_values)
            return
            
        # Apply window function
        windowed_data = audio_data * self.window
        
        # Compute FFT
        fft = np.fft.fft(windowed_data)
        magnitude = np.abs(fft[:len(fft)//2])
        
        # Enhanced processing for better visualization
        # Apply logarithmic scaling to compress dynamic range
        magnitude = np.log10(magnitude + 1e-10)  # Add small constant to avoid log(0)
        
        # Frequency weighting to emphasize musical content
        freqs = np.fft.fftfreq(BLOCK_SIZE, 1/SAMPLE_RATE)[:BLOCK_SIZE//2]
        weights = np.ones_like(freqs)
        
        # Boost low frequencies (20-200 Hz) - bass (reduced sensitivity)
        low_mask = (freqs >= 20) & (freqs <= 200)
        weights[low_mask] *= 1.2  # Reduced from 1.5
        
        # Boost mid frequencies (200-2000 Hz) - vocals (reduced sensitivity)
        mid_mask = (freqs > 200) & (freqs <= 2000)
        weights[mid_mask] *= 1.1  # Reduced from 1.2
        
        # Slightly boost highs (2000-8000 Hz) (reduced sensitivity)
        high_mask = (freqs > 2000) & (freqs <= 8000)
        weights[high_mask] *= 1.0  # Reduced from 1.1
        
        # Apply weighting
        magnitude = magnitude * weights
        
        # Normalize to get good visualization range
        if np.max(magnitude) > np.min(magnitude):
            # Use robust normalization
            magnitude = (magnitude - np.min(magnitude)) / (np.max(magnitude) - np.min(magnitude))
            
            # Apply gamma correction for better visual dynamics (less sensitive)
            magnitude = np.power(magnitude, 0.6)  # Less aggressive than before (was 0.4)
            
            # Scale more conservatively for less sensitivity
            magnitude = magnitude * 0.6  # Reduced from 0.8
        else:
            magnitude = np.zeros_like(magnitude)
            
        # Clip to reasonable range
        magnitude = np.clip(magnitude, 0, 1.5)  # More conservative range
        
        # Map frequencies to bars
        bar_values = self.map_to_bars(magnitude)
        
        # Add temporal smoothing for smoother animation
        if hasattr(self, 'previous_bars'):
            # Smooth with previous frame for less choppy animation
            bar_values = self.previous_bars * 0.6 + bar_values * 0.4
        self.previous_bars = bar_values.copy()
        
        # Final scaling based on actual audio level (allow for dramatic peaks)
        bar_values = np.clip(bar_values, 0, 1.0)  # Allow higher peaks (was 0.4)
        
        # Scale based on RMS more gently for smoother animation
        if rms > 1e-3:
            amplitude_multiplier = min(1.5, 0.3 + (rms * 4))  # Less aggressive for smoother motion
            bar_values = bar_values * amplitude_multiplier
        
        # Update visualizer (thread-safe)
        GLib.idle_add(self.visualizer.update_visualization, bar_values)
        
    def map_to_bars(self, fft_data):
        """Map FFT data to visualization bars with dramatic individual differences"""
        bar_values = np.zeros(DESKTOP_BARS)
        
        for i, (start_freq, end_freq) in enumerate(self.bar_freqs):
            # Find frequency bin indices
            start_idx = int(start_freq * BLOCK_SIZE / SAMPLE_RATE)
            end_idx = int(end_freq * BLOCK_SIZE / SAMPLE_RATE)
            
            # Ensure valid indices
            start_idx = max(0, min(start_idx, len(fft_data) - 1))
            end_idx = max(start_idx + 1, min(end_idx, len(fft_data)))
            
            if start_idx < end_idx:
                # Use peak instead of RMS for more dramatic differences
                freq_range_data = fft_data[start_idx:end_idx]
                bar_values[i] = np.max(freq_range_data)  # Peak gives more variation
                
                # Boost frequencies based on musical importance and position
                # Center frequencies (most musical content) get biggest boost
                freq_center = (start_freq + end_freq) / 2
                bar_position = i  # Bar index (0 to 79)
                center_position = DESKTOP_BARS / 2  # Position 40
                distance_from_center = abs(bar_position - center_position) / center_position  # 0 to 1
                
                # Boost center bars (most musical content) more than edge bars
                if distance_from_center < 0.2:  # Center 20% of bars
                    # Core vocal and guitar range - MAXIMUM boost
                    if 1200 <= freq_center <= 5000:
                        bar_values[i] *= 3.0  # Maximum boost for most important frequencies
                    else:
                        bar_values[i] *= 2.5
                elif distance_from_center < 0.4:  # Next 20% toward edges
                    # Important musical content
                    if 600 <= freq_center <= 6000:
                        bar_values[i] *= 2.0
                    else:
                        bar_values[i] *= 1.5
                elif distance_from_center < 0.6:  # Outer regions
                    # Some musical content
                    bar_values[i] *= 1.2
                else:  # Edge bars - least musical content
                    # Very low bass and very high treble - minimal boost
                    bar_values[i] *= 0.8
                    
            else:
                bar_values[i] = fft_data[start_idx] if start_idx < len(fft_data) else 0
        
        # Apply non-linear scaling for more dramatic differences
        bar_values = np.power(bar_values, 1.3)  # Emphasize peaks more
        
        # Remove neighbor smoothing completely for maximum individual differences
        return bar_values
    
    def start(self):
        """Start audio processing with speaker output capture"""
        try:
            self.running = True
            
            # Get all available devices
            available_devices = sd.query_devices()
            logger.info("Scanning for speaker output devices...")
            
            # Priority order for speaker audio capture
            speaker_audio_candidates = []
            
            for i, device_info in enumerate(available_devices):
                device_name = device_info['name'].lower()
                inputs = device_info['max_input_channels']
                
                if inputs > 0:
                    # HIGHEST PRIORITY: Actual built-in speakers (what we want most!)
                    if 'speaker' in device_name and 'controller' in device_name and 'hdmi' not in device_name and 'displayport' not in device_name:
                        speaker_audio_candidates.insert(0, (i, device_info, "built-in-speaker"))
                        logger.info(f"🔊 Found BUILT-IN SPEAKER {i}: {device_info['name']}")
                    
                    # HIGH PRIORITY: Other speaker monitors 
                    elif any(keyword in device_name for keyword in ['speaker', 'built-in', 'analog']):
                        if 'monitor' in device_name or 'output' in device_name:
                            speaker_audio_candidates.insert(1, (i, device_info, "speaker-monitor"))
                            logger.info(f"🔊 Found SPEAKER MONITOR {i}: {device_info['name']}")
                    
                    # MEDIUM PRIORITY: HDMI/DisplayPort (secondary outputs)
                    elif any(keyword in device_name for keyword in ['hdmi', 'displayport']):
                        if 'monitor' in device_name or 'output' in device_name:
                            speaker_audio_candidates.append((i, device_info, "hdmi-monitor"))
                            logger.info(f"🔊 Found HDMI MONITOR {i}: {device_info['name']}")
                    
                    # LOWER PRIORITY: Generic monitor devices 
                    elif 'monitor' in device_name and 'sink' in device_name:
                        speaker_audio_candidates.append((i, device_info, "sink-monitor"))
                        logger.info(f"🔊 Found sink monitor {i}: {device_info['name']}")
                    
                    # LOW PRIORITY: Loopback devices 
                    elif 'loopback' in device_name:
                        speaker_audio_candidates.append((i, device_info, "loopback"))
                        logger.info(f"🔊 Found loopback device {i}: {device_info['name']}")
                    
                    # FALLBACK: Virtual devices 
                    elif device_name in ['pipewire', 'default'] and inputs >= 64:
                        speaker_audio_candidates.append((i, device_info, "virtual"))
                        logger.info(f"🔊 Found virtual device {i}: {device_info['name']}")
            
            logger.info(f"Found {len(speaker_audio_candidates)} speaker audio candidates")
            
            # Try each speaker audio candidate
            for device_id, device_info, device_type in speaker_audio_candidates:
                try:
                    logger.info(f"🔄 Trying {device_type} device {device_id}: {device_info['name']}")
                    
                    # Try different sample rates if device fails
                    sample_rates = [SAMPLE_RATE, 48000, 44100, 96000, 22050]
                    for sr in sample_rates:
                        try:
                            self.stream = sd.InputStream(
                                samplerate=sr,
                                blocksize=BLOCK_SIZE,
                                channels=min(CHANNELS, device_info['max_input_channels']),
                                callback=self.audio_callback,
                                dtype=np.float32,
                                device=device_id
                            )
                            self.stream.start()
                            logger.info(f"✅ SUCCESS: Using SPEAKER AUDIO from device {device_id} at {sr}Hz: {device_info['name']}")
                            return  # Success!
                        except Exception as sr_e:
                            if sr == sample_rates[-1]:  # Last attempt
                                raise sr_e
                            continue
                            
                except Exception as e:
                    logger.warning(f"❌ Failed device {device_id} ({device_type}): {e}")
                    if self.stream:
                        self.stream.close()
                        self.stream = None
                    continue
            
            # If no direct speaker devices work, try PulseAudio sink monitors (BEST for speaker output)
            logger.info("🔄 Trying PulseAudio sink monitors...")
            try:
                import subprocess
                result = subprocess.run(['pactl', 'list', 'short', 'sources'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    monitor_sources = []
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line and '.monitor' in line:
                            parts = line.split('\t')
                            if len(parts) >= 2:
                                source_name = parts[1].strip()
                                # HIGHEST PRIORITY: The actual speaker monitor we found!
                                if 'Speaker__sink.monitor' in source_name:
                                    monitor_sources.insert(0, source_name)
                                    logger.info(f"🔊 Found ACTUAL SPEAKER MONITOR: {source_name}")
                                # High priority: other speaker/output monitors
                                elif any(keyword in source_name.lower() for keyword in ['speaker', 'analog', 'built-in', 'hdmi']):
                                    monitor_sources.insert(-1 if monitor_sources else 0, source_name)
                                    logger.info(f"🔊 Found PRIORITY PA speaker monitor: {source_name}")
                                else:
                                    monitor_sources.append(source_name)
                                    logger.info(f"🔊 Found PA monitor: {source_name}")
                    
                    # Try each monitor source (speaker monitors first)
                    for source_name in monitor_sources:
                        try:
                            logger.info(f"🔄 Trying PA monitor: {source_name}")
                            
                            # Try different sample rates for PA sources too
                            sample_rates = [48000, 44100, SAMPLE_RATE, 96000, 22050]  # Start with 48kHz (common for PA)
                            for sr in sample_rates:
                                try:
                                    self.stream = sd.InputStream(
                                        samplerate=sr,
                                        blocksize=BLOCK_SIZE,
                                        channels=CHANNELS,
                                        callback=self.audio_callback,
                                        dtype=np.float32,
                                        device=source_name
                                    )
                                    self.stream.start()
                                    logger.info(f"✅ SUCCESS: Using PA speaker monitor at {sr}Hz: {source_name}")
                                    return
                                except Exception as sr_e:
                                    if sr == sample_rates[-1]:  # Last attempt
                                        raise sr_e
                                    continue
                                    
                        except Exception as e:
                            logger.warning(f"❌ PA monitor failed {source_name}: {e}")
                            if self.stream:
                                self.stream.close()
                                self.stream = None
                            continue
            
            except Exception as e:
                logger.warning(f"Could not query PulseAudio: {e}")
            
            # Last resort: just show minimal baseline (better than fake data)
            logger.warning("❌ No speaker audio available - showing minimal baseline")
            self._start_minimal_baseline()
            
        except Exception as e:
            logger.error(f"Failed to start audio processor: {e}")
            self.running = False
            self._start_minimal_baseline()
            
    def _start_minimal_baseline(self):
        """Show minimal baseline when no audio is available"""
        def minimal_callback():
            if not self.running:
                return False
                
            # Just show very small baseline bars (no fake animation)
            baseline_data = np.ones(DESKTOP_BARS) * 0.01  # Tiny baseline
            GLib.idle_add(self.visualizer.update_visualization, baseline_data)
            return True
        
        # Update baseline at low frequency to save CPU
        GLib.timeout_add(100, minimal_callback)  # 10 FPS
        self.running = True
        logger.info("Minimal baseline started - bars will show small baseline until audio plays")
            
    def _start_test_pattern(self):
        """Generate test pattern when no audio is available"""
        def test_callback():
            if not self.running:
                return False
                
            # Generate animated test pattern that looks more like real audio
            import time
            t = time.time()
            test_data = np.zeros(DESKTOP_BARS)
            
            for i in range(DESKTOP_BARS):
                # Create varied frequencies and phases for each bar
                freq1 = 0.8 + (i % 7) * 0.15  # Different base frequency per bar group
                freq2 = 0.4 + (i % 5) * 0.08   # Secondary modulation
                phase = i * 0.2  # Phase offset for wave effect
                
                # Multiple sine waves for complex motion
                wave1 = np.sin(t * freq1 + phase)
                wave2 = np.sin(t * freq2 + phase * 0.7) * 0.6
                wave3 = np.sin(t * 0.3 + i * 0.1) * 0.4  # Slow global wave
                
                # Combine waves with varying amplitudes
                amplitude = (wave1 + wave2 + wave3) * 0.3 + 0.5
                
                # Add some randomness to make it look more natural
                noise = (np.random.random() - 0.5) * 0.1
                amplitude += noise
                
                # Ensure positive values with good range
                test_data[i] = max(0.1, min(1.5, amplitude))
            
            # Add some bass-like behavior (lower frequencies higher)
            for i in range(min(15, DESKTOP_BARS)):
                test_data[i] *= 1.3 + (15 - i) * 0.05
            
            GLib.idle_add(self.visualizer.update_visualization, test_data)
            return True
        
        # Update test pattern at 30 FPS
        GLib.timeout_add(33, test_callback)
        self.running = True
        logger.info("Enhanced test pattern started - showing animated music-like visualization")
    
    def stop(self):
        """Stop audio processing"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("Audio processor stopped")

class PythonVisualizer:
    def __init__(self):
        self.audio_data = np.zeros(DESKTOP_BARS)
        self.smoothed_data = np.zeros(DESKTOP_BARS)
        self.peak_data = np.zeros(DESKTOP_BARS)
        self.fall_speed = np.zeros(DESKTOP_BARS)
        
        # Smoothing factors for smoother, less choppy animation
        self.smoothing_factor = 0.75  # Much more smoothing for smoother animation (was 0.4)
        self.peak_decay = 0.92  # Slower decay for smoother transitions (was 0.85)  
        self.gravity = 0.015  # Less gravity for gentler drops (was 0.03)
        
        # Create drawing area
        self.area = Gtk.DrawingArea()
        self.area.set_hexpand(True)
        self.area.set_vexpand(False)
        self.area.set_size_request(-1, VISUALIZER_HEIGHT)
        self.area.set_draw_func(self.draw_visualizer)
        
    def update_visualization(self, data):
        """Update visualization data"""
        if data is None or len(data) == 0:
            return False
            
        # Apply smoothing
        self.smoothed_data = (self.smoothed_data * self.smoothing_factor + 
                             data * (1 - self.smoothing_factor))
        
        # Peak detection with gravity
        for i in range(len(self.smoothed_data)):
            if self.smoothed_data[i] > self.peak_data[i]:
                self.peak_data[i] = self.smoothed_data[i]
                self.fall_speed[i] = 0
            else:
                self.fall_speed[i] += self.gravity
                self.peak_data[i] = max(0, self.peak_data[i] - self.fall_speed[i])
        
        self.audio_data = self.smoothed_data.copy()
        self.area.queue_draw()
        return False
        
    def draw_visualizer(self, area, cr, width, height, user_data=None):
        """Enhanced visualization with centered bars that grow from middle"""
        # Clear background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        
        if width <= 0 or len(self.audio_data) == 0:
            return
            
        # Calculate optimal bar dimensions for full desktop width
        available_width = width - (2 * MARGIN)
        total_spacing = (DESKTOP_BARS - 1) * BAR_SPACING
        bar_width = max(BAR_MIN_WIDTH, 
                       min(BAR_MAX_WIDTH, 
                           (available_width - total_spacing) // DESKTOP_BARS))
        
        # Adjust spacing to perfectly fill width
        remaining_width = available_width - (DESKTOP_BARS * bar_width)
        actual_spacing = remaining_width / max(1, DESKTOP_BARS - 1) if DESKTOP_BARS > 1 else 0
        
        # Start from left margin
        start_x = MARGIN
        
        # Baseline for bars (center of visualizer area for up+down growth)
        center_y = height // 2  # Center of the visualizer area
        max_bar_height = height // 2 - 20  # Max height from center to edge minus margins
        
        # Create gradient pattern across full width
        for i in range(DESKTOP_BARS):
            if i >= len(self.audio_data):
                break
                
            x = start_x + i * (bar_width + actual_spacing)
            
            # Bar height calculation with corner tapering effect
            raw_intensity = self.audio_data[i]
            
            # Apply corner tapering effect (mountain shape)
            center = DESKTOP_BARS / 2
            distance_from_center = abs(i - center) / center  # 0 to 1
            taper_factor = 1.0 - (distance_from_center * 0.5)  # Reduce by up to 50% at corners
            tapered_intensity = raw_intensity * taper_factor
            
            bar_height = max(2, tapered_intensity * max_bar_height)  # Minimum 2px height
            
            # Bar positions - grow both up and down from center
            bar_top_y = center_y - bar_height  # Grow upward from center
            bar_bottom_y = center_y + bar_height  # Grow downward from center
            total_bar_height = bar_height * 2  # Total height is double (up + down)
            
            # Clean monochrome color scheme like the image
            r, g, b, base_alpha = CLEAN_COLOR
            
            # Dynamic alpha based on intensity for depth
            intensity = min(1.0, tapered_intensity * 2.0)  # Use tapered intensity
            alpha = 0.4 + (intensity * 0.6)  # Range from 0.4 to 1.0
            
            # Add glow effect for active bars
            if intensity > 0.05:
                # Draw glow (larger, more transparent)
                glow_width = bar_width + 6
                glow_height = total_bar_height + 12
                glow_x = x - 3
                glow_top_y = bar_top_y - 6
                
                cr.set_source_rgba(r, g, b, alpha * 0.2)
                self._draw_rounded_rect(cr, glow_x, glow_top_y, glow_width, glow_height, BAR_ROUNDNESS + 3)
                cr.fill()
            
            # Draw main bar (growing both up and down from center)
            cr.set_source_rgba(r, g, b, alpha)
            self._draw_rounded_rect(cr, x, bar_top_y, bar_width, total_bar_height, BAR_ROUNDNESS)
            cr.fill()
            
            # Remove peak indicators for cleaner upward-only look
    
    def _draw_rounded_rect(self, cr, x, y, width, height, radius):
        """Draw a rounded rectangle with proper radius handling"""
        # Ensure radius doesn't exceed half the width or height
        radius = min(radius, width/2, height/2)
        
        if radius <= 0 or width <= 0 or height <= 0:
            # Fallback to regular rectangle if radius is too small
            cr.rectangle(x, y, width, height)
            return
            
        cr.new_sub_path()
        # Top-left corner
        cr.arc(x + radius, y + radius, radius, np.pi, 3 * np.pi / 2)
        # Top-right corner
        cr.arc(x + width - radius, y + radius, radius, 3 * np.pi / 2, 0)
        # Bottom-right corner
        cr.arc(x + width - radius, y + height - radius, radius, 0, np.pi / 2)
        # Bottom-left corner
        cr.arc(x + radius, y + height - radius, radius, np.pi / 2, np.pi)
        cr.close_path()

class DesktopAudioVisualizer(widgets.Window):
    """Enhanced desktop-wide audio visualizer with beautiful styling"""
    
    def __init__(self, monitor_id: int = 0):
        self.visualizer = PythonVisualizer()
        self.audio_processor = PythonAudioProcessor(self.visualizer)
        
        # Create full-width container
        self.container = widgets.Box(
            orientation="horizontal",
            hexpand=True,
            vexpand=False,
            halign="fill",
            valign="end",
            css_classes=["visualizer-container"]
        )
        self.container.append(self.visualizer.area)
        
        super().__init__(
            namespace=f"ignis_desktop_visualizer_{monitor_id}",
            monitor=monitor_id,
            exclusivity="ignore",
            child=self.container,
            anchor=["left", "right"],
            css_classes=["desktop-audio-visualizer"],
            layer="background"
        )
        
        # Start audio processing with delay
        GLib.timeout_add(1500, self._delayed_start)
        
    def _delayed_start(self):
        """Start audio processing with delay"""
        try:
            self.audio_processor.start()
            logger.info("Desktop audio visualizer started successfully")
        except Exception as e:
            logger.error(f"Failed to start audio visualizer: {e}")
        return False
        
    def close(self):
        """Clean up resources"""
        try:
            self.audio_processor.stop()
            logger.info("Desktop audio visualizer stopped")
        except Exception as e:
            logger.error(f"Error stopping audio visualizer: {e}")
        super().close()

def desktop_audio_visualizer(monitor_id: int = 0) -> DesktopAudioVisualizer:
    """Create a beautiful desktop-wide audio visualizer
    
    Features:
    - 80 bars spanning full desktop width
    - Beautiful gradient colors with glow effects
    - Rounded corners and smooth animations
    - Peak detection with gravity
    - Pure Python - no external dependencies
    
    Args:
        monitor_id: Monitor to display on (default: 0)
        
    Returns:
        DesktopAudioVisualizer window instance
    """
    return DesktopAudioVisualizer(monitor_id)