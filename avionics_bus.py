"""
FEU Alabang - Department of Computer Engineering
Final Laboratory Examination: Multi-Sensor Avionics Bus Simulator
Target Platform: GitHub Codespaces (Linux / Python 3.11+)
DESCRIPTION: This module simulates a high-frequency avionics sensor bus (MIL-STD-1553/ARINC 429).
It polls hardware peripherals concurrently, formats telemetry buffers, and executes
downstream signal normalization for flight control algorithms.
"""
import time
import json
import threading
import os
import sys
import random
import math

# =====================================================================
# SYSTEM INITIALIZATION & HARDWARE PROFILE LOADING
# =====================================================================
CONFIG_FILE = "hardware_config.json"
if not os.path.exists(CONFIG_FILE):
    print("[FATAL ERROR] Hardware configuration not found!")
    print("Execute: python3 fault_seed.py --id 20231000031 before running diagnostics.")
    sys.exit(1)

with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)

print(f"[SYSTEM] Avionics Bus initialized for Signature: {CONFIG.get('signature_hash', 'UNKNOWN')}")

# =====================================================================
# MODULE 1: TELEMETRY ENCAPSULATION & BUFFERING
# =====================================================================
class TelemetryBuffer:
    """Encapsulates time-series hardware voltage frames prior to bus transmission."""

    def __init__(self, channel_id: str, frame_buffer: list = None):
        self.channel_id = channel_id
        self.frame_buffer = frame_buffer if frame_buffer is not None else []
        self.dropped_packets = 0

    def push_frame(self, timestamp: float, voltage_level: float):
        """Appends a timestamped hardware reading to the transmission queue."""
        packet = {
            "ts": round(timestamp, 4),
            "val": round(voltage_level, 4),
            "status": "NOMINAL"
        }
        self.frame_buffer.append(packet)
        
        max_capacity = CONFIG.get("buffer_overflow_threshold", 25)
        if len(self.frame_buffer) > max_capacity:
            raise MemoryError(
                f"[{CONFIG['signature_hash']}] Hardware Buffer Overflow on Channel {self.channel_id}! "
                f"Current Buffer Size: {len(self.frame_buffer)} (Max: {max_capacity})"
            )

    def flush_buffer(self) -> int:
        """Clears transmitted frames and returns count of cleared packets."""
        count = len(self.frame_buffer)
        self.frame_buffer.clear()
        return count

# =====================================================================
# MODULE 2: POLYMORPHIC HARDWARE PERIPHERALS
# =====================================================================
class AvionicsPeripheral:
    """Abstract Base Class representing a standardized bus peripheral."""

    def __init__(self, pin_number: int, peripheral_name: str):
        self.pin_number = pin_number
        self.peripheral_name = peripheral_name
        self.buffer = TelemetryBuffer(f"CH_{pin_number}_{peripheral_name}")
        self.is_active = True

    def poll_raw_voltage(self) -> float:
        """
        Reads physical pin ADC registers.
        Contract: Must return a floating-point voltage between 0.0V and 5.0V.
        """
        return 0.0

    def execute_self_test(self) -> bool:
        return self.is_active


class LiDARPeripheral(AvionicsPeripheral):
    """Optical laser distance measurement peripheral."""

    def poll_raw_voltage(self) -> float:
        base_voltage = 2.5 + (math.sin(time.time()) * 0.5)
        self.buffer.push_frame(time.time(), base_voltage)
        return base_voltage


class GPSPeripheral(AvionicsPeripheral):
    """Satellite navigation receiver peripheral."""

    def poll_raw_voltage(self) -> float:
        voltage = 3.3 + random.uniform(-0.05, 0.05)
        self.buffer.push_frame(time.time(), voltage)
        return voltage


class IMUPeripheral(AvionicsPeripheral):
    """Inertial Measurement Unit (6-DoF Accelerometer/Gyroscope)."""

    def poll_raw_voltage(self) -> float:
        drift_factor = CONFIG.get("imu_voltage_drift", 1.0)
        simulated_voltage = 1.8 * (drift_factor / 5.0)
        
        if drift_factor > 2.0:
            error_packet = {
                "ERR_CODE": "IMU_AXIS_DRIFT",
                "RAW_VAL": simulated_voltage,
                "FAULT_ID": CONFIG["signature_hash"]
            }
            self.buffer.push_frame(time.time(), 0.0)
            return 0.0
                
        self.buffer.push_frame(time.time(), simulated_voltage)
        return simulated_voltage

# =====================================================================
# MODULE 3: CONCURRENT BUS CONTROLLER & SIGNAL PROCESSING
# =====================================================================
class AvionicsBusMaster:
    """Manages asynchronous polling threads and shared master telemetry registers."""

    def __init__(self):
        self.peripherals = [
            LiDARPeripheral(pin_number=10, peripheral_name="LIDAR_FRONT"),
            GPSPeripheral(pin_number=12, peripheral_name="GPS_MAIN"),
            IMUPeripheral(pin_number=14, peripheral_name="IMU_NAV")
        ]
        self.active_bus_register = {}
        self.total_cycles_executed = 0
        self.lock = threading.Lock()

    def _async_polling_worker(self, peripheral: AvionicsPeripheral, poll_cycles: int):
        """Worker thread executing high-frequency register polling and normalization."""
        for _ in range(poll_cycles):
            if not peripheral.is_active:
                continue
                        
            raw_signal = peripheral.poll_raw_voltage()
                    
            time.sleep(CONFIG.get("bus_race_delay_sec", 0.002))
                    
            normalized_signal = (raw_signal * 5.0) / 3.3
                    
            channel_key = peripheral.peripheral_name
            
            with self.lock:
                current_state = self.active_bus_register.get(channel_key, {
                    "packets_received": 0,
                    "latest_voltage": 0.0,
                    "status": "INIT"
                })
                        
                time.sleep(0.001)
                        
                current_state["packets_received"] += 1
                current_state["latest_voltage"] = round(normalized_signal, 4)
                current_state["status"] = "SYNCED"
                        
                self.active_bus_register[channel_key] = current_state
                self.total_cycles_executed += 1

    def begin_flight_telemetry_loop(self, cycles_per_peripheral: int = 10):
        """Spawns concurrent worker threads across all active avionics peripherals."""
        print(f"--- Launching Avionics Bus Master [Threads: {len(self.peripherals)}] ---")
        thread_pool = []
            
        for peripheral in self.peripherals:
            t = threading.Thread(
                target=self._async_polling_worker,
                args=(peripheral, cycles_per_peripheral),
                name=f"Thread-{peripheral.peripheral_name}"
            )
            thread_pool.append(t)
            t.start()
                
        for t in thread_pool:
            t.join()
                
        print("--- Telemetry Loop Terminated ---")
        print(f"Total Register Writes: {self.total_cycles_executed}")
        self._dump_bus_diagnostics()

    def _dump_bus_diagnostics(self):
        print("\n--- FINAL AVIONICS BUS REGISTER STATE ---")
        for channel, data in self.active_bus_register.items():
            print(f"Channel [{channel:12}] -> Packets: {data['packets_received']:2} | Latest: {data['latest_voltage']}V | Status: {data['status']}")


if __name__ == "__main__":
    bus_master = AvionicsBusMaster()
    try:
        bus_master.begin_flight_telemetry_loop(cycles_per_peripheral=12)
    except Exception as e:
        print(f"\n[CRITICAL SYSTEM FAULT] Unhandled Exception during flight loop:")
        print(f"{type(e).__name__}: {str(e)}")
        sys.exit(1)