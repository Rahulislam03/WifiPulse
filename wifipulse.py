#!/usr/bin/env python3
import socket
import threading
import subprocess
import platform
from datetime import datetime

# সাধারণ নেটওয়ার্ক সার্ভিস পোর্টের তালিকা
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    53: "DNS",
    80: "HTTP (Router Admin)",
    443: "HTTPS (Secure Admin)",
    1900: "UPnP",
    8080: "HTTP-Proxy"
}

def print_banner():
    print("=" * 60)
    print("        📶 WIFI PULSE - AUTOMATIC NETWORK INSPECTOR       ")
    print("=" * 60)

# ১. বর্তমান কানেক্টেড ওয়াইফাইয়ের IP, Subnet এবং Gateway অটো-ডিটেক্ট করা
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

# ২. অপারেটিং সিস্টেম অনুযায়ী Ping চেক করা
def ping_host(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '500', ip] if platform.system().lower() == 'windows' else ['ping', param, '1', '-W', '1', ip]
    
    try:
        output = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output.returncode == 0
    except Exception:
        return False

# ৩. পোর্ট স্ক্যানিং
open_ports = []
def scan_port(target_ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.8)
        result = sock.connect_ex((target_ip, port))
        if result == 0:
            service = COMMON_PORTS.get(port, "Unknown")
            open_ports.append((port, service))
        sock.close()
    except Exception:
        pass

# ৪. মূল কাজ
def main():
    print_banner()
    print("[*] Detecting connected Wi-Fi Network...")
    
    local_ip, gateway_ip, subnet_base = get_auto_network_info()
    if not local_ip:
        return

    print(f"[✔] Connected Local IP : {local_ip}")
    print(f"[✔] Router Gateway IP  : {gateway_ip}")
    print(f"[✔] Target Subnet      : {subnet_base}0/24")
    print("-" * 60)

    # রাউটারের খোলা পোর্ট চেক করা
    print(f"[*] Scanning Router/Gateway ({gateway_ip}) Open Ports...")
    threads = []
    for port in COMMON_PORTS.keys():
        t = threading.Thread(target=scan_port, args=(gateway_ip, port))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

    if open_ports:
        for port, service in open_ports:
            print(f"    [+] Port {port:<5} : OPEN ({service})")
    else:
        print("    [-] No standard open ports found on router.")

    print("-" * 60)
    # পুরো ওয়াইফাই নেটওয়ার্কের ১ থেকে ২৫৪ সকল IP স্ক্যান
    print("[*] Discovering ALL Active Devices on connected Wi-Fi (Range .1 to .254)...")
    active_hosts = []
    
    def check_host(ip_last):
        target = f"{subnet_base}{ip_last}"
        if ping_host(target):
            active_hosts.append(target)

    ping_threads = []
    for i in range(1, 255):  # ১ থেকে ২৫৪ পর্যন্ত সম্পূর্ণ সাবনেট স্ক্যান
        t = threading.Thread(target=check_host, args=(i,))
        ping_threads.append(t)
        t.start()

    for t in ping_threads:
        t.join()

    print(f"\n[✔] Found {len(active_hosts)} active devices on this Wi-Fi:")
    for host in sorted(active_hosts, key=lambda x: int(x.split('.')[-1])):
        device_label = " (Router)" if host == gateway_ip else (" (Your Device)" if host == local_ip else "")
        print(f"    [•] {host}{device_label}")

    print("\n[*] Scan Completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
