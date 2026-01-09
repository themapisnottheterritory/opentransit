"""
Tests for AVL server NMEA parsing.
"""

import pytest
from datetime import datetime

# Import from avl module
import sys
sys.path.insert(0, '..')

from avl.server import (
    nmea_checksum,
    nmea_to_decimal,
    parse_gprmc,
    GPRMCData
)


class TestNMEAChecksum:
    """Tests for NMEA checksum validation."""
    
    def test_valid_checksum(self):
        """Valid sentence should pass checksum."""
        sentence = "$GPRMC,123456.00,A,2848.3180,N,09659.1200,W,25.0,180.0,080125,,,A,V1234*XX"
        # Calculate what checksum should be
        data = sentence.split('*')[0][1:]  # Remove $ and everything after *
        expected = 0
        for c in data:
            expected ^= ord(c)
        
        valid_sentence = f"$GPRMC,123456.00,A,2848.3180,N,09659.1200,W,25.0,180.0,080125,,,A,V1234*{expected:02X}"
        result = nmea_checksum(valid_sentence)
        assert result[1] == result[2]
    
    def test_missing_asterisk(self):
        """Sentence without * should raise ValueError."""
        with pytest.raises(ValueError, match="missing '\\*'"):
            nmea_checksum("$GPRMC,123456.00,A,2848.3180,N,09659.1200,W")
    
    def test_invalid_hex_checksum(self):
        """Invalid hex checksum should raise ValueError."""
        with pytest.raises(ValueError, match="not valid hex"):
            nmea_checksum("$GPRMC,123456.00,A*ZZ")


class TestNMEAToDecimal:
    """Tests for NMEA coordinate conversion."""
    
    def test_latitude_conversion(self):
        """Test converting NMEA latitude to decimal."""
        # 2848.3180 = 28 degrees, 48.318 minutes
        # = 28 + (48.318 / 60) = 28.80530
        result = nmea_to_decimal(2848.3180)
        assert abs(result - 28.80530) < 0.0001
    
    def test_longitude_conversion(self):
        """Test converting NMEA longitude to decimal."""
        # 09659.1200 = 96 degrees, 59.12 minutes
        # = 96 + (59.12 / 60) = 96.98533
        result = nmea_to_decimal(9659.1200)
        assert abs(result - 96.98533) < 0.0001
    
    def test_zero_minutes(self):
        """Test coordinate with zero minutes."""
        result = nmea_to_decimal(2800.0000)
        assert result == 28.0
    
    def test_precision(self):
        """Test that result has proper precision."""
        result = nmea_to_decimal(2848.318765)
        # Should be rounded to 7 decimal places
        assert len(str(result).split('.')[1]) <= 7


class TestParseGPRMC:
    """Tests for GPRMC sentence parsing."""
    
    def test_valid_gprmc(self):
        """Test parsing a valid GPRMC sentence."""
        sentence = "$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,21.5,270.0,080125,,,A,1234*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.unit_id == "1234"
        assert abs(result.latitude - 28.80530) < 0.001
        assert abs(result.longitude - (-96.98533)) < 0.001
        assert result.speed_mph == pytest.approx(21.5 * 1.150779, rel=0.01)
        assert result.heading == 270.0
        assert result.status == "A"
    
    def test_southern_hemisphere(self):
        """Test parsing coordinates in southern hemisphere."""
        sentence = "$GPRMC,143025.00,A,2848.3180,S,09659.1200,W,0,0,080125,,,A,1234*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.latitude < 0  # South = negative
    
    def test_eastern_hemisphere(self):
        """Test parsing coordinates in eastern hemisphere."""
        sentence = "$GPRMC,143025.00,A,2848.3180,N,09659.1200,E,0,0,080125,,,A,1234*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.longitude > 0  # East = positive
    
    def test_invalid_sentence_type(self):
        """Non-GPRMC sentence should return None."""
        sentence = "$GPGGA,143025.00,2848.3180,N,09659.1200,W,1,08,0.9,100.0,M,0,M,,*5A"
        result = parse_gprmc(sentence)
        assert result is None
    
    def test_missing_lat_data(self):
        """GPRMC without latitude should return None."""
        sentence = "$GPRMC,143025.00,V,,N,09659.1200,W,0,0,080125,,,N,1234*5A"
        result = parse_gprmc(sentence)
        assert result is None
    
    def test_empty_speed(self):
        """Empty speed field should default to 0."""
        sentence = "$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,,270.0,080125,,,A,1234*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.speed_mph == 0.0
    
    def test_empty_heading(self):
        """Empty heading field should default to 0."""
        sentence = "$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,21.5,,080125,,,A,1234*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.heading == 0.0
    
    def test_unit_id_extraction(self):
        """Test extracting unit ID from field 13."""
        # Unit ID with checksum attached
        sentence = "$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,21.5,270.0,080125,,,A,UNIT01*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.unit_id == "UNIT"  # First 4 chars
    
    def test_short_unit_id(self):
        """Test handling unit ID shorter than 4 chars."""
        sentence = "$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,21.5,270.0,080125,,,A,BUS*5A"
        result = parse_gprmc(sentence)
        
        assert result is not None
        assert result.unit_id == "BUS"


class TestGPRMCData:
    """Tests for GPRMCData class."""
    
    def test_repr(self):
        """Test string representation."""
        data = GPRMCData(
            unit_id="1234",
            latitude=28.80530,
            longitude=-96.98533,
            speed_mph=25.0,
            heading=180.0,
            timestamp=datetime.now(),
            status="A",
            raw="$GPRMC..."
        )
        
        repr_str = repr(data)
        assert "1234" in repr_str
        assert "28.80530" in repr_str
        assert "25.0mph" in repr_str
