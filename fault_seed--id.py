import json
import argparse
import hashlib

def main():
    parser = argparse.ArgumentParser(description="Avionics Hardware Fault Seed Profile Generator")
    parser.add_argument("--id", type=str, required=True, help="8-digit Student ID")
    args = parser.parse_args()

    # Generate a unique validation signature based on your student ID
    hash_object = hashlib.md5(args.id.encode())
    signature = f"FEU_A_{hash_object.hexdigest()[:12].upper()}"

    # Recreate the exact hardware configuration parameters expected by avionics_bus.py
    config_data = {
        "signature_hash": signature,
        "buffer_overflow_threshold": 25,
        "imu_voltage_drift": 1.2,          # Kept in nominal bounds to clear errors gracefully
        "bus_race_delay_sec": 0.002
    }

    # Write out the file required by Module 1 initialization
    with open("hardware_config.json", "w") as f:
        json.dump(config_data, f, indent=4)
   
    print(f"[SUCCESS] Hardware profile locked for Student ID {args.id}")
    print(f"Generated Profile Signature: {signature}")

if __name__ == "__main__":
    main()