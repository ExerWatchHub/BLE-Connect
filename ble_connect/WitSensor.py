import struct
import logging
import threading
from enum import IntEnum
from typing import Optional, List
from uuid import UUID

# Constants
class WitOp:
    READ_0xFF = 0xFF
    READ_0xAA = 0xAA
    READ_0x27 = 0x27
    UNLOCK_REG_0x69 = 0x69
    SET_RETURN_RATE_0x03 = 0x03
    FIELD_CALIBRATION_0x01 = 0x01


class WitCalibration:
    MAG_FIELD_CALIBRATION_0x07 = 0x07
    END_0x00 = 0x00
    ACCEL_CALIBRATION_0x01 = 0x01


class WitPacket:
    PACKET_START_0x55 = 0x55
    DATA_0x61 = 0x61
    READ_RETURN_0x71 = 0x71


class WitField:
    TEMPERATURE_0x40 = 0x40
    VERSION_NUMBER_0x2E = 0x2E
    FIRMWARE_VERSION_NUMBER_0x47 = 0x47
    HX = 0x3A
    HY = 0x3B
    HZ = 0x3C
    Q1_0x51 = 0x51
    Q2_0x52 = 0x52
    Q3_0x53 = 0x53
    Q4_0x54 = 0x54
    BATTERY_0x64 = 0x64
    SIGNAL_VALUE = 0x64
    MAGNETOMETER = 0x72


class Point3D:
    def __init__(self, values: List[float]):
        self.x = values[0] if len(values) > 0 else 0.0
        self.y = values[1] if len(values) > 1 else 0.0
        self.z = values[2] if len(values) > 2 else 0.0


class SensorData:
    def __init__(self, device=None):
        self.device = device
        self.acc: Optional[Point3D] = None
        self.gyr: Optional[Point3D] = None
        self.mag: Optional[Point3D] = None


class WitSensorStrategy:
    # Class constants
    SERVICE_UUID = UUID("0000ffe5-0000-1000-8000-00805f9a34fb")
    READ_UUID = UUID("0000ffe4-0000-1000-8000-00805f9a34fb")
    NOTIFIABLE_UUID = UUID("0000ffe4-0000-1000-8000-00805f9a34fb")
    
    UPDATE_DELAY = 10.0  # seconds
    
    def __init__(self):
        self.device = None
        self.timer = None
        self.logger = logging.getLogger("WitSensor")
        
    @staticmethod
    def is_witmotion_sensor(services) -> bool:
        """Check if device is a WitMotion sensor based on services"""
        res = any(service.uuid == WitSensorStrategy.SERVICE_UUID for service in services)
        if res:
            logging.info("Identified as WitMotion sensor")
        return res
    
    def initialize(self, device, imu_data_repository=None, ble_repository=None, bt_adapter_name=None):
        """Initialize the sensor strategy"""
        self.device = device
        self.logger.info("Initializing WitMotion sensor")
        
        # Enable notifications
        device.enable_notifications(self.NOTIFIABLE_UUID)
        
        # Start periodic updates
        self._schedule_update(0.25)  # Initial delay of 250ms
    
    def _schedule_update(self, delay: float):
        """Schedule periodic sensor updates"""
        if self.timer:
            self.timer.cancel()
        
        self.timer = threading.Timer(delay, self._update_task)
        self.timer.daemon = True
        self.timer.start()
    
    def _update_task(self):
        """Periodic update task"""
        try:
            self.read_battery_level()
            self.read_config()
            self.read_temperature()
        except Exception as e:
            self.logger.error(f"Error in update task: {e}")
        finally:
            self._schedule_update(self.UPDATE_DELAY)
    
    def process_data(self, characteristic, data: bytes) -> Optional[SensorData]:
        """Process incoming BLE data"""
        if not data or len(data) < 2:
            return None
        
        if characteristic.uuid != self.NOTIFIABLE_UUID:
            return None
        
        bytes_list = bytearray(data)
        
        # Remove any invalid data before the first packet start
        while bytes_list and bytes_list[0] != WitPacket.PACKET_START_0x55:
            bytes_list.pop(0)
        
        if not bytes_list:
            return None
        
        # Split into individual packets
        packets = []
        current_packet_start = 0
        
        for i in range(1, len(bytes_list)):
            if bytes_list[i] == WitPacket.PACKET_START_0x55 and (i - current_packet_start) >= 20:
                packets.append(bytes(bytes_list[current_packet_start:i]))
                current_packet_start = i
        
        # Add the last packet
        packets.append(bytes(bytes_list[current_packet_start:]))
        
        # Process each packet
        result_data = None
        for packet in packets:
            if len(packet) < 2:
                continue
            
            if packet[1] == WitPacket.DATA_0x61:
                result_data = self._decode_data_packet(packet)
            elif packet[1] == WitPacket.READ_RETURN_0x71:
                self._decode_return_packet(packet)
        
        return result_data
    
    def _decode_return_packet(self, data: bytes):
        """Decode a return packet from the sensor"""
        if len(data) < 4:
            return
        
        flag0 = data[0]
        flag1 = data[1]
        value_type = data[2]
        separator = data[3]
        
        if value_type == WitField.BATTERY_0x64:
            # Parse battery level
            value = struct.unpack_from('<I', data, 4)[0]
            eq_percent = self._get_eq_percent(value / 100.0)
            if self.device and hasattr(self.device, 'battery_level'):
                self.device.battery_level = eq_percent
            self.logger.info(f"Battery level set to: {eq_percent}")
        
        elif value_type == WitField.TEMPERATURE_0x40:
            value = struct.unpack_from('<I', data, 4)[0]
            temperature = value / 100.0
            self.logger.info(f"Temperature set to: {temperature}")
        
        elif value_type == WitField.VERSION_NUMBER_0x2E:
            # Parse version/config data
            pass
        
        else:
            if len(data) >= 8:
                value = struct.unpack_from('<I', data, 4)[0]
                self.logger.info(f"Received unknown return data: {value}")
    
    def _decode_data_packet(self, data: bytes) -> Optional[SensorData]:
        """Decode a data packet containing sensor readings"""
        if len(data) < 22:
            return None
        
        # Unpack all values (little-endian shorts)
        values = struct.unpack_from('<Hbhhhhhhhhh', data, 0)
        
        flag0 = values[0] & 0xFF
        flag1 = (values[0] >> 8) & 0xFF
        
        reg_ax = values[2]
        reg_ay = values[3]
        reg_az = values[4]
        reg_wx = values[5]
        reg_wy = values[6]
        reg_wz = values[7]
        reg_angle_x = values[8]
        reg_angle_y = values[9]
        reg_angle_z = values[10]
        
        # Convert to physical units
        acc_x = (reg_ax / 32768.0) * 16.0
        acc_y = (reg_ay / 32768.0) * 16.0
        acc_z = (reg_az / 32768.0) * 16.0
        
        as_x = (reg_wx / 32768.0) * 2000.0
        as_y = (reg_wy / 32768.0) * 2000.0
        as_z = (reg_wz / 32768.0) * 2000.0
        
        angle_x = (reg_angle_x / 32768.0) * 180.0
        angle_y = (reg_angle_y / 32768.0) * 180.0
        angle_z = (reg_angle_z / 32768.0) * 180.0
        
        # Create sensor data object
        result = SensorData(device=self.device)
        result.acc = Point3D([acc_x, acc_y, acc_z])
        result.gyr = Point3D([as_x, as_y, as_z])
        
        return result
    
    def cleanup(self):
        """Clean up resources"""
        if self.timer:
            self.timer.cancel()
            self.timer = None
    
    # Command methods
    def send_protocol_data(self, data: bytes):
        """Send protocol data to the sensor"""
        if self.device:
            self.device.write_characteristic(self.READ_UUID, data)
    
    def unlock_reg(self):
        """Unlock register for configuration"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, WitOp.UNLOCK_REG_0x69, 0x88, 0xB5
        ]))
    
    def applied_calibration(self):
        """Apply calibration"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, 
            WitOp.FIELD_CALIBRATION_0x01, WitCalibration.ACCEL_CALIBRATION_0x01, 0x00
        ]))
    
    def start_field_calibration(self):
        """Start magnetic field calibration"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA,
            WitOp.FIELD_CALIBRATION_0x01, WitCalibration.MAG_FIELD_CALIBRATION_0x07, 0x00
        ]))
    
    def end_field_calibration(self):
        """End magnetic field calibration"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA,
            WitOp.FIELD_CALIBRATION_0x01, WitCalibration.END_0x00, 0x00
        ]))
    
    def set_return_rate(self, rate: int):
        """Set the sensor return rate"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, WitOp.SET_RETURN_RATE_0x03, rate, 0x00
        ]))
    
    def read_config(self):
        """Read sensor configuration"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, WitOp.READ_0x27, 
            WitField.VERSION_NUMBER_0x2E, 0x00
        ]))
    
    def read_battery_level(self):
        """Read battery level"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, WitOp.READ_0x27, 
            WitField.BATTERY_0x64, 0x00
        ]))
    
    def read_temperature(self):
        """Read temperature"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, WitOp.READ_0x27, 
            WitField.TEMPERATURE_0x40, 0x00
        ]))
    
    def read_mag_type(self):
        """Read magnetometer type"""
        self.send_protocol_data(bytes([
            WitOp.READ_0xFF, WitOp.READ_0xAA, WitOp.READ_0x27, 
            WitField.MAGNETOMETER, 0x00
        ]))
    
    @staticmethod
    def _get_eq_percent(eq: float) -> float:
        """Calculate battery percentage from voltage"""
        if eq > 5.5:
            x = [6.5, 6.8, 7.35, 7.75, 8.5, 8.8]
            y = [0.0, 10.0, 30.0, 60.0, 90.0, 100.0]
        else:
            x = [3.4, 3.5, 3.68, 3.7, 3.73, 3.77, 3.79, 3.82, 3.87, 3.93, 3.96, 3.99]
            y = [0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0, 75.0, 90.0, 100.0]
        
        return WitSensorStrategy._interp(eq, x, y)
    
    @staticmethod
    def _interp(a: float, x: List[float], y: List[float]) -> float:
        """Linear interpolation"""
        if a < x[0]:
            return y[0]
        if a > x[-1]:
            return y[-1]
        
        for i in range(len(y) - 1):
            if a <= x[i + 1]:
                return y[i] + ((a - x[i]) / (x[i + 1] - x[i])) * (y[i + 1] - y[i])
        
        return y[-1]