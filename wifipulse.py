#!/usr/bin/env python3
import socket
import threading
import subprocess
import platform
import time
from datetime import datetime

# ১. টার্মিনাল কালার কোড (ANSI Colors)
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# পোর্ট ও সার্ভিস লিস্ট
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    53: "DNS",
    80: "HTTP",
    443: "HTTPS",
    1900: "UPnP",
    8080: "HTTP-Proxy"
}

# ২. MAC Vendor OUI ডিকশনারি (Local Database)
MAC_VENDORS = {
    "50:C7:BF": "TP-Link",
    "A4:C3:F0": "Apple",
    "78:4F:43": "Apple",
    "DC:A6:32": "Raspberry Pi",
    "B8:27:EB": "Raspberry Pi",
    "00:1A:2B": "Cisco",
    "E8:65:D4": "Xiaomi",
    "FC:EC:DA": "Ubiquiti / Unifi",
    "00:00:5E": "IANA Reserved"
}

def print_banner():
    print(CYAN + "=" * 65 + RESET)
    print(GREEN + "        📶 WIFI PULSE - ADVANCED NETWORK & SECURITY INSPECTOR       " + RESET)
    print(CYAN + "=" * 65 + RESET)

def get_auto_network_info():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    if local_ip == "127.0.0.1":
        print(RED + "[!] Error: Wi-Fi connection not detected." + RESET)
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

def test_wifi_speed(gateway_ip):
    print(YELLOW + f"[*] Testing Wi-Fi Latency (Ping to Gateway: {gateway_ip})..." + RESET)
    start_time = time.time()
    if ping_host(gateway_ip):
        latency = (time.time() - start_time) * 1000
        return f"{latency:.2f} ms"
    return "High Latency / Timeout"

def get_mac_address(ip):
    try:
        cmd = ["arp", "-a", ip] if platform.system().lower() == 'windows' else ["arp", "-n", ip]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
        for line in output.split("\n"):
            if ip in line:
                parts = line.split()
                for part in parts:
                    if (":" in part or "-" in part) and len(part) in (17, 14):
                        return part.upper()
    except Exception:
        pass
    return "Unknown MAC"

# Vendor Lookup
def get_vendor(mac):
    if mac and mac != "Unknown MAC":
        oui = mac.replace("-", ":")[:8]
        return MAC_VENDORS.get(oui, "Unknown Vendor / Generic Device")
    return "Unknown Vendor"

def get_hostname(ip):
    try:
        host_info = socket.gethostbyaddr(ip)
        return host_info[0]
    except Exception:
        return "Unknown Device"

# Banner Grabbing
def grab_banner(target_ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((target_ip, port))
        
        if port in [80, 8080]:
            sock.sendall(b"HEAD / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
        
        banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
        sock.close()
        if banner:
            first_line = banner.split("\n")[0]
            return first_line[:40]
    except Exception:
        pass
    return "No Banner Response"

def scan_device_ports_and_banners(target_ip):
    open_ports = []
    for port, service in COMMON_PORTS.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.4)
            result = sock.connect_ex((target_ip, port))
            if result == 0:
                banner_info = grab_banner(target_ip, port)
                open_ports.append({
                    "port": port,
                    "service": service,
                    "banner": banner_info
                })
            sock.close()
        except Exception:
            pass
    return open_ports

# Local Vulnerability Check
def check_router_security(gateway_ip, open_ports):
    warnings = []
    open_port_numbers = [p["port"] for p in open_ports]
    
    if 21 in open_port_numbers:
        warnings.append("FTP (Port 21) is open. Unencrypted file transfer detected.")
    if 23 in open_port_numbers:
        warnings.append("TELNET (Port 23) is open. High Risk: Plaintext remote connection!")
    if 80 in open_port_numbers and 443 not in open_port_numbers:
        warnings.append("Router Web Admin panel uses unencrypted HTTP (Port 80) only.")
    if 1900 in open_port_numbers:
        warnings.append("UPnP (Port 1900) is active. Potential vulnerability entry point.")
        
    return warnings

def main():
    print_banner()
    print(YELLOW + "[*] Detecting connected Wi-Fi Network..." + RESET)
    
    local_ip, gateway_ip, subnet_base = get_auto_network_info()
    if not local_ip:
        return

    print(GREEN + f"[✔] Connected Local IP : {local_ip}" + RESET)
    print(GREEN + f"[✔] Router Gateway IP  : {gateway_ip}" + RESET)
    print(GREEN + f"[✔] Target Subnet      : {subnet_base}0/24" + RESET)
    
    wifi_speed = test_wifi_speed(gateway_ip)
    print(GREEN + f"[✔] Wi-Fi Latency Speed: {wifi_speed}" + RESET)
    print(CYAN + "-" * 65 + RESET)

    print(YELLOW + "[*] Discovering Devices, Vendors, Banners & Security Checks (1-254)..." + RESET)
    print("    Please wait a few moments...\n")
    
    active_devices = []
    lock = threading.Lock()

    def process_host(ip_last):
        target = f"{subnet_base}{ip_last}"
        if ping_host(target):
            hostname = get_hostname(target)
            mac_addr = get_mac_address(target)
            vendor = get_vendor(mac_addr)
            open_ports = scan_device_ports_and_banners(target)
            
            security_alerts = []
            if target == gateway_ip:
                security_alerts = check_router_security(gateway_ip, open_ports)
            
            with lock:
                active_devices.append({
                    "ip": target,
                    "name": hostname,
                    "mac": mac_addr,
                    "vendor": vendor,
                    "ports": open_ports,
                    "alerts": security_alerts
                })

    threads = []
    for i in range(1, 255):
        t = threading.Thread(target=process_host, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(GREEN + f"[✔] Found {len(active_devices)} active device(s) on this Wi-Fi:\n" + RESET)
    
    for dev in sorted(active_devices, key=lambda x: int(x['ip'].split('.')[-1])):
        label = " (Router)" if dev['ip'] == gateway_ip else (" (Your Device)" if dev['ip'] == local_ip else "")
        
        print(CYAN + f" 📌 IP Address  : {dev['ip']}{label}" + RESET)
        print(f"    Device Name : {dev['name']}")
        print(f"    MAC Address : {dev['mac']}")
        print(GREEN + f"    Vendor/Brand: {dev['vendor']}" + RESET)
        
        if dev['ports']:
            print(YELLOW + "    Open Ports & Banners:" + RESET)
            for p in dev['ports']:
                banner_text = f" ({p['banner']})" if p['banner'] != "No Banner Response" else ""
                print(f"      • Port {p['port']:<5} [{p['service']}]{banner_text}")
        else:
            print("    Open Ports  : None found")

        if dev['alerts']:
            print(RED + "    ⚠️ Security Alerts:" + RESET)
            for alert in dev['alerts']:
                print(RED + f"      [!] {alert}" + RESET)

        print("    " + "-" * 45)

    print(GREEN + "\n[*] Scan Completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S") + RESET)

if __name__ == "__main__":
    main()
