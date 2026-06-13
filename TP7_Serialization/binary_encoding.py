import json
import struct

def encode_device(device_id, hostname, ip_address, services, level=""):
    parts = []

    parts.append(struct.pack(">I", device_id))

    hostname_bytes = hostname.encode("utf-8")
    parts.append(struct.pack(">H", len(hostname_bytes)))
    parts.append(hostname_bytes)

    ip_bytes = ip_address.encode("utf-8")
    parts.append(struct.pack(">H", len(ip_bytes)))
    parts.append(ip_bytes)

    parts.append(struct.pack(">H", len(services)))

    for service in services:
        service_bytes = service.encode("utf-8")
        parts.append(struct.pack(">H", len(service_bytes)))
        parts.append(service_bytes)

    level_bytes = level.encode("utf-8")
    parts.append(struct.pack(">H", len(level_bytes)))
    parts.append(level_bytes)

    return b"".join(parts)

def decode_device(binary_data):
    offset = 0

    device_id = struct.unpack_from(">I", binary_data, offset)[0]
    offset += 4

    hostname_len = struct.unpack_from(">H", binary_data, offset)[0]
    offset += 2
    hostname = binary_data[offset:offset + hostname_len].decode("utf-8")
    offset += hostname_len

    ip_len = struct.unpack_from(">H", binary_data, offset)[0]
    offset += 2
    ip_address = binary_data[offset:offset + ip_len].decode("utf-8")
    offset += ip_len

    services_count = struct.unpack_from(">H", binary_data, offset)[0]
    offset += 2

    services = []

    for i in range(services_count):
        service_len = struct.unpack_from(">H", binary_data, offset)[0]
        offset += 2
        service = binary_data[offset:offset + service_len].decode("utf-8")
        offset += service_len
        services.append(service)

    level_len = struct.unpack_from(">H", binary_data, offset)[0]
    offset += 2
    level = binary_data[offset:offset + level_len].decode("utf-8")

    return {
        "device_id": device_id,
        "hostname": hostname,
        "ip_address": ip_address,
        "services": services,
        "level": level or "default"
    }

if __name__ == "__main__":
    binary = encode_device(
        10,
        "server-prod",
        "192.168.1.10",
        ["http", "ssh", "dns"],
        "critical"
    )

    json_data = json.dumps({
        "device_id": 10,
        "hostname": "server-prod",
        "ip_address": "192.168.1.10",
        "services": ["http", "ssh", "dns"],
        "level": "critical"
    }).encode("utf-8")

    print(f"Binary size: {len(binary)} bytes")
    print(f"JSON size: {len(json_data)} bytes")
    print(f"Ratio JSON/Binary: {len(json_data) / len(binary):.2f}x")

    decoded = decode_device(binary)
    print("Decoded data:")
    print(decoded)