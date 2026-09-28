#!/usr/bin/env python3
import socket
import threading
import subprocess
import platform
from datetime import datetime

COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    53: "DNS",
    80: "HTTP",
    443: "HTTPS",
    8080: "HTTP-Proxy"
}

def print_banner():
    print("=" * 65)
    print("        📶 WIFI PULSE - AUTOMATIC NETWORK INSPECTOR       ")
    print("=" * 65)

def get_auto_network_info():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    if local_ip == "127.0.0.1":
        print("[!] Error: Wi-Fi connection not detected.")
        return None, None, None

    ip_parts = local_ip.split(".")
    subnet_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."
    gateway_ip = f"{subnet_base}1"
    
    return local_ip, gateway_ip, subnet_base

def ping_host(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '500', ip] if platform.system().lower() == 'windows' else ['ping', param, '1', '-W', '1', ip]
    
    try:
        output = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output.returncode == 0
    except Exception:
        return False

# IP থেকে ডিভাইসের নাম (Hostname) খোঁজার ফাংশন
def get_hostname(ip):
    try:
        host_info = socket.gethostbyaddr(ip)
        return host_info[0]
    except Exception:
        return "Unknown Device"

# নির্দিষ্ট IP-এর ওপেন পোর্ট স্ক্যান করার ফাংশন
def scan_device_ports(target_ip):
    open_ports = []
    for port, service in COMMON_PORTS.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((target_ip, port))
            if result == 0:
                open_ports.append(f"{port}/{service}")
            sock.close()
        except Exception:
            pass
    return open_ports

def main():
    print_banner()
    print("[*] Detecting connected Wi-Fi Network...")
    
    local_ip, gateway_ip, subnet_base = get_auto_network_info()
    if not local_ip:
        return

    print(f"[✔] Connected Local IP : {local_ip}")
    print(f"[✔] Router Gateway IP  : {gateway_ip}")
    print(f"[✔] Target Subnet      : {subnet_base}0/24")
    print("-" * 65)

    print("[*] Discovering Active Devices & Open Ports (Range .1 to .254)...")
    print("    Please wait a few moments...\n")
    
    active_devices = []
    lock = threading.Lock()

    def process_host(ip_last):
        target = f"{subnet_base}{ip_last}"
        if ping_host(target):
            hostname = get_hostname(target)
            open_ports = scan_device_ports(target)
            
            with lock:
                active_devices.append({
                    "ip": target,
                    "name": hostname,
                    "ports": open_ports
                })

    threads = []
    for i in range(1, 255):
        t = threading.Thread(target=process_host, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"[✔] Found {len(active_devices)} active device(s) on this Wi-Fi:\n")
    
    # ফলাফল প্রিন্ট করা
    for dev in sorted(active_devices, key=lambda x: int(x['ip'].split('.')[-1])):
        label = " (Router)" if dev['ip'] == gateway_ip else (" (Your Device)" if dev['ip'] == local_ip else "")
        ports_str = ", ".join(dev['ports']) if dev['ports'] else "None found"
        
        print(f" 📌 IP Address : {dev['ip']}{label}")
        print(f"    Device Name: {dev['name']}")
        print(f"    Open Ports : {ports_str}")
        print("    " + "-" * 40)

    print("\n[*] Scan Completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
