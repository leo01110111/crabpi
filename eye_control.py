"""
Raspberry Pi eye control for 7-segment display eyes via shift registers.

Drive two digits (eyes) with data/latch/clock GPIO pins. Use look_left(),
look_right(), and look_forward() to set eye direction.
"""

# Two numbering systems:
#
# 1. Logical segment index (0-6): 0=A, 1=B, 2=C, 3=D, 4=E, 5=F, 6=G.
#    We use these in SEGMENTS_* below. Same for both eyes.
#
# 2. Hardware bit index (0-15): the bit in the 16-bit shift register.
#    Different per digit. D1_SEGMENTS / D2_SEGMENTS map logical index -> bit.
#
# Right eye (digit 1): A=bit2, B=bit3, C=bit1, D=bit0, E=bit6, F=bit5, G=bit7
# Left eye (digit 2):  A=bit9, B=bit10, C=bit8, D=bit15, E=bit13, F=bit12, G=bit14
D1_SEGMENTS = (2, 3, 1, 0, 6, 5, 7)   # logical 0..6 -> bit for right eye (G = 7)
D1_DP = 4
D2_SEGMENTS = (9, 10, 8, 15, 13, 12, 14)  # logical 0..6 -> bit for left eye (G = 14)
D2_DP = 11

# Look presets: tuples of logical segment indices (0=A .. 6=G).
# Each look is applied to BOTH eyes (we pass the same tuple for digit 1 and 2).
SEGMENTS_FORWARD = (0, 1, 2, 3, 4, 5)   # A, B, C, D, E, F (open)
SEGMENTS_LEFT = (4, 5, 6)   # E, F, G
SEGMENTS_RIGHT = (1, 2, 6)  # B, C, G
# Closed = G only. (6,) means logical index 6 = G -> right eye bit 7, left eye bit 14
SEGMENTS_CLOSED = (6,)
SEGMENTS_OFF = ()

#Only call look functions when you want to update the eyes. 
#No need to call look_forward() if you're already looking forward.

class EyeControl:
    """
    Control two 7-segment "eyes" driven by shift registers on a Raspberry Pi.

    Pass the GPIO pin numbers (BCM) for the shift register data, latch, and
    clock lines. Then call look_forward(), look_left(), or look_right() to
    update the display.
    """

    def __init__(
        self,
        data_pin: int,
        latch_pin: int,
        clock_pin: int,
        *,
        use_BCM: bool = True,
    ) -> None:
        """
        Initialize eye control with GPIO pins for the shift register.

        Args:
            data_pin: GPIO pin for serial data.
            latch_pin: GPIO pin for latch (storage register clock).
            clock_pin: GPIO pin for shift register clock.
            use_BCM: If True (default), use BCM numbering; else use board.
        """
        try:
            import RPi.GPIO as GPIO
        except ImportError:
            raise ImportError(
                'RPi.GPIO is required for eye control. '
                'Install with: pip install RPi.GPIO'
            ) from None

        self._GPIO = GPIO
        self._data_pin = data_pin
        self._latch_pin = latch_pin
        self._clock_pin = clock_pin

        mode = GPIO.BCM if use_BCM else GPIO.BOARD
        self._GPIO.setmode(mode)
        self._GPIO.setwarnings(False)
        self._GPIO.setup(data_pin, GPIO.OUT, initial=GPIO.LOW)
        self._GPIO.setup(latch_pin, GPIO.OUT, initial=GPIO.LOW)
        self._GPIO.setup(clock_pin, GPIO.OUT, initial=GPIO.LOW)

    def _bits_for_segments(
        self,
        d1_segment_indices: tuple[int, ...],
        d2_segment_indices: tuple[int, ...],
    ) -> int:
        """Build 16-bit value from logical segment indices (0-6) for both eyes."""
        d1_pins = D1_SEGMENTS
        d2_pins = D2_SEGMENTS
        value = 0
        for i in d1_segment_indices:
            if 0 <= i < len(d1_pins):
                value |= 1 << d1_pins[i]
        for i in d2_segment_indices:
            if 0 <= i < len(d2_pins):
                value |= 1 << d2_pins[i]
        return value

    def _update_shift_registers(self, output_bits: int) -> None:
        """Shift out a 16-bit value to the daisy-chained shift registers."""
        GPIO = self._GPIO
        GPIO.output(self._latch_pin, GPIO.LOW)
        high_byte = (output_bits >> 8) & 0xFF
        low_byte = output_bits & 0xFF
        for byte in (high_byte, low_byte):
            for _ in range(8):
                GPIO.output(self._clock_pin, GPIO.LOW)
                GPIO.output(self._data_pin, GPIO.HIGH if (byte & 0x80) else GPIO.LOW)
                GPIO.output(self._clock_pin, GPIO.HIGH)
                byte <<= 1
        GPIO.output(self._latch_pin, GPIO.HIGH)

    def look_forward(self) -> None:
        """Set both eyes to look forward (full open)."""
        bits = self._bits_for_segments(SEGMENTS_FORWARD, SEGMENTS_FORWARD)
        self._update_shift_registers(bits)

    def look_left(self) -> None:
        """Set both eyes to look left (left-side segments lit)."""
        bits = self._bits_for_segments(SEGMENTS_LEFT, SEGMENTS_LEFT)
        self._update_shift_registers(bits)

    def look_right(self) -> None:
        """Set both eyes to look right (right-side segments lit)."""
        bits = self._bits_for_segments(SEGMENTS_RIGHT, SEGMENTS_RIGHT)
        self._update_shift_registers(bits)

    def look_closed(self) -> None:
        """Set both eyes to look closed (all segments off)."""
        bits = self._bits_for_segments(SEGMENTS_CLOSED, SEGMENTS_CLOSED)
        self._update_shift_registers(bits)
    
    def look_off(self) -> None:
        """Set both eyes to look off (all segments off)."""
        bits = self._bits_for_segments(SEGMENTS_OFF, SEGMENTS_OFF)
        self._update_shift_registers(bits)
    
    def close(self) -> None:
        """Release GPIO and clean up. Call when done with the controller."""
        self._GPIO.cleanup()
