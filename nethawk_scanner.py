#!/usr/bin/env python3
"""
Advanced Port Scanner - Nethawk - Enterprise-grade network reconnaissance tool
Author: Zeeshan01001
Version: 2.0.0
License: MIT
"""

import socket
import sys
import threading
import argparse
import json
import csv
import time
import subprocess
import struct
import random
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import xml.etree.ElementTree as ET

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class AdvancedPortScanner:
    def __init__(self, targets, timeout=1, stealth=False, verbose=False):
        self.targets = targets if isinstance(targets, list) else [targets]
        self.timeout = timeout
        self.stealth = stealth
        self.verbose = verbose
        self.results = {}
        self.scan_stats = {
            'total_hosts': 0,
            'total_ports': 0,
            'open_ports': 0,
            'filtered_ports': 0,
            'closed_ports': 0,
            'start_time': None,
            'end_time': None
        }
        self.services = self.load_service_database()
        self.lock = threading.Lock()

    def load_service_database(self):
        """Load service database for port identification"""
        services = {
            21: {'name': 'FTP', 'description': 'File Transfer Protocol'},
            22: {'name': 'SSH', 'description': 'Secure Shell'},
            23: {'name': 'Telnet', 'description': 'Telnet Protocol'},
            25: {'name': 'SMTP', 'description': 'Simple Mail Transfer Protocol'},
            53: {'name': 'DNS', 'description': 'Domain Name System'},
            80: {'name': 'HTTP', 'description': 'Hypertext Transfer Protocol'},
            110: {'name': 'POP3', 'description': 'Post Office Protocol v3'},
            143: {'name': 'IMAP', 'description': 'Internet Message Access Protocol'},
            443: {'name': 'HTTPS', 'description': 'HTTP Secure'},
            993: {'name': 'IMAPS', 'description': 'IMAP over SSL'},
            995: {'name': 'POP3S', 'description': 'POP3 over SSL'},
            3389: {'name': 'RDP', 'description': 'Remote Desktop Protocol'},
            5432: {'name': 'PostgreSQL', 'description': 'PostgreSQL Database'},
            3306: {'name': 'MySQL', 'description': 'MySQL Database'},
            1433: {'name': 'MSSQL', 'description': 'Microsoft SQL Server'},
            135: {'name': 'RPC', 'description': 'Microsoft RPC'},
            139: {'name': 'NetBIOS', 'description': 'NetBIOS Session Service'},
            445: {'name': 'SMB', 'description': 'Server Message Block'},
            8080: {'name': 'HTTP-Alt', 'description': 'HTTP Alternative'},
            8443: {'name': 'HTTPS-Alt', 'description': 'HTTPS Alternative'},
        }
        return services

    def get_common_ports(self, preset='top100'):
        """Get common port lists"""
        top100 = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 993, 995,
            1723, 3306, 3389, 5900, 8080, 8443, 25565, 5432, 1433, 6379, 27017,
            445, 993, 995, 587, 465, 143, 110, 995, 993, 1433, 3306, 5432,
            6379, 27017, 2049, 111, 2048, 135, 139, 445, 1024, 1025, 1026,
            1027, 1028, 1029, 1030, 1080, 1433, 1521, 2082, 2083, 2086, 2087,
            2095, 2096, 3128, 3306, 3389, 5060, 5432, 5500, 5632, 5900, 6000,
            6001, 6646, 7070, 8000, 8008, 8080, 8443, 8888, 9090, 9100, 9999,
            10000, 32768, 49152, 49153, 49154, 49155, 49156, 49157
        ]
        
        top1000 = list(range(1, 1001))
        all_ports = list(range(1, 65536))
        
        if preset == 'top100':
            return sorted(list(set(top100)))[:100]
        elif preset == 'top1000':
            return top1000
        elif preset == 'all':
            return all_ports
        else:
            return top100

    def parse_ports(self, port_spec):
        """Parse port specification"""
        if port_spec in ['top100', 'top1000', 'all']:
            return self.get_common_ports(port_spec)
        
        ports = []
        for part in port_spec.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                ports.extend(range(start, end + 1))
            else:
                ports.append(int(part))
        
        return sorted(list(set(ports)))

    def resolve_hostname(self, target):
        """Resolve hostname to IP address"""
        try:
            ip = socket.gethostbyname(target)
            if ip != target:
                print(f"{Colors.BLUE}[RESOLVE]{Colors.END} {target} -> {ip}")
            return ip
        except socket.gaierror:
            print(f"{Colors.RED}[ERROR]{Colors.END} Cannot resolve {target}")
            return None

    def scan_network_range(self, cidr):
        """Scan network range from CIDR notation"""
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            return [str(ip) for ip in network.hosts()]
        except ValueError:
            print(f"{Colors.RED}[ERROR]{Colors.END} Invalid CIDR notation: {cidr}")
            return []

    def grab_banner(self, ip, port):
        """Attempt to grab service banner"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Send appropriate probe based on port
            if port == 80:
                sock.send(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
            elif port == 21:
                pass  # FTP sends banner immediately
            elif port == 22:
                pass  # SSH sends banner immediately
            else:
                sock.send(b"\r\n")
            
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            sock.close()
            return banner[:100] if banner else None
        except:
            return None

    def detect_os(self, ip):
        """Basic OS detection via TTL analysis"""
        try:
            if sys.platform.startswith('win'):
                result = subprocess.run(['ping', '-n', '1', ip], 
                                      capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['ping', '-c', '1', ip], 
                                      capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                output = result.stdout
                if 'ttl=64' in output.lower() or 'ttl=255' in output.lower():
                    return "Linux/Unix"
                elif 'ttl=128' in output.lower():
                    return "Windows"
                elif 'ttl=32' in output.lower():
                    return "Windows 9x/NT"
                else:
                    return "Unknown"
        except:
            pass
        return "Unknown"

    def scan_port(self, ip, port):
        """Scan a single port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                # Port is open
                service_info = self.services.get(port, {'name': 'Unknown', 'description': 'Unknown Service'})
                banner = self.grab_banner(ip, port) if not self.stealth else None
                
                port_info = {
                    'status': 'open',
                    'service': service_info['name'],
                    'description': service_info['description'],
                    'banner': banner
                }
                
                banner_text = f" [{banner[:50]}...]" if banner else ""
                print(f"{Colors.GREEN}[OPEN]{Colors.END} {ip}:{port} ({service_info['name']}){banner_text}")
                
                with self.lock:
                    self.scan_stats['open_ports'] += 1
                
                sock.close()
                return port, port_info
            else:
                # Port is closed/filtered
                if self.verbose:
                    print(f"{Colors.RED}[CLOSED]{Colors.END} {ip}:{port}")
                
                with self.lock:
                    self.scan_stats['closed_ports'] += 1
                
                sock.close()
                return None
                
        except socket.timeout:
            if self.verbose:
                print(f"{Colors.YELLOW}[FILTERED]{Colors.END} {ip}:{port}")
            
            with self.lock:
                self.scan_stats['filtered_ports'] += 1
            
            return None
        except Exception as e:
            if self.verbose:
                print(f"{Colors.RED}[ERROR]{Colors.END} {ip}:{port} - {e}")
            return None
        finally:
            if self.stealth:
                time.sleep(random.uniform(0.1, 0.5))

    def scan_host(self, target, ports, max_threads):
        """Scan all ports on a single host"""
        # Resolve hostname
        ip = self.resolve_hostname(target)
        if not ip:
            return None

        print(f"{Colors.BLUE}[INFO]{Colors.END} Scanning host: {ip}")
        
        # Detect OS
        if not self.stealth:
            print(f"{Colors.BLUE}[INFO]{Colors.END} Detecting OS for {ip}...")
            os_info = self.detect_os(ip)
        else:
            os_info = "Unknown"

        host_result = {
            'ip': ip,
            'hostname': target if target != ip else None,
            'os': os_info,
            'ports': {},
            'scan_time': datetime.now().isoformat()
        }

        # Scan ports using thread pool
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_port = {executor.submit(self.scan_port, ip, port): port for port in ports}
            
            for future in as_completed(future_to_port):
                result = future.result()
                if result:
                    port, port_info = result
                    host_result['ports'][port] = port_info

        return host_result

    def print_summary(self):
        """Print scan summary"""
        duration = self.scan_stats['end_time'] - self.scan_stats['start_time']
        
        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"                        SCAN SUMMARY")
        print(f"{'='*60}{Colors.END}")
        print(f"Scan Duration: {Colors.CYAN}{duration:.2f} seconds{Colors.END}")
        print(f"Total Hosts: {Colors.CYAN}{self.scan_stats['total_hosts']}{Colors.END}")
        print(f"Total Ports Scanned: {Colors.CYAN}{self.scan_stats['total_ports']}{Colors.END}")
        print(f"Open Ports: {Colors.GREEN}{self.scan_stats['open_ports']}{Colors.END}")
        print(f"Filtered Ports: {Colors.YELLOW}{self.scan_stats['filtered_ports']}{Colors.END}")
        print(f"Closed Ports: {Colors.RED}{self.scan_stats['closed_ports']}{Colors.END}")
        
        # Count services
        service_count = {}
        for host_data in self.results.values():
            for port_data in host_data['ports'].values():
                service = port_data['service']
                service_count[service] = service_count.get(service, 0) + 1
        
        if service_count:
            print(f"\n{Colors.BOLD}TOP SERVICES FOUND:{Colors.END}")
            for service, count in sorted(service_count.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {Colors.CYAN}{service}: {count}{Colors.END}")

    def export_results(self, filename_prefix, export_format='json'):
        """Export scan results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        export_data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'targets': self.targets,
                'scan_stats': self.scan_stats,
                'duration': self.scan_stats['end_time'] - self.scan_stats['start_time']
            },
            'results': self.results
        }

        if export_format == 'json':
            filename = f"{filename_prefix}_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"{Colors.GREEN}[EXPORT]{Colors.END} Results saved to {filename}")

        elif export_format == 'csv':
            filename = f"{filename_prefix}_{timestamp}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Host', 'IP', 'Port', 'Status', 'Service', 'Banner', 'OS'])
                
                for host, data in self.results.items():
                    for port, port_info in data['ports'].items():
                        writer.writerow([
                            data.get('hostname', ''),
                            data['ip'],
                            port,
                            port_info['status'],
                            port_info['service'],
                            port_info.get('banner', ''),
                            data['os']
                        ])
            print(f"{Colors.GREEN}[EXPORT]{Colors.END} Results saved to {filename}")

        elif export_format == 'xml':
            filename = f"{filename_prefix}_{timestamp}.xml"
            root = ET.Element('scan_results')
            
            # Add scan info
            scan_info = ET.SubElement(root, 'scan_info')
            for key, value in export_data['scan_info'].items():
                elem = ET.SubElement(scan_info, key)
                elem.text = str(value)
            
            # Add results
            results = ET.SubElement(root, 'results')
            for host, data in self.results.items():
                host_elem = ET.SubElement(results, 'host', name=host)
                
                ip_elem = ET.SubElement(host_elem, 'ip')
                ip_elem.text = data['ip']
                
                os_elem = ET.SubElement(host_elem, 'os')
                os_elem.text = data['os']
                
                ports_elem = ET.SubElement(host_elem, 'ports')
                for port, port_info in data['ports'].items():
                    port_elem = ET.SubElement(ports_elem, 'port', number=str(port))
                    for key, value in port_info.items():
                        if value:
                            elem = ET.SubElement(port_elem, key)
                            elem.text = str(value)
            
            tree = ET.ElementTree(root)
            tree.write(filename, encoding='utf-8', xml_declaration=True)
            print(f"{Colors.GREEN}[EXPORT]{Colors.END} Results saved to {filename}")

    def run_scan(self, port_spec, max_threads=100):
        """Main scanning function"""
        self.scan_stats['start_time'] = time.time()
        
        # Parse ports
        ports = self.parse_ports(port_spec)
        
        # Process targets (handle network ranges)
        all_hosts = []
        for target in self.targets:
            if '/' in target:  # CIDR notation
                all_hosts.extend(self.scan_network_range(target))
            else:
                all_hosts.append(target)

        self.scan_stats['total_hosts'] = len(all_hosts)
        self.scan_stats['total_ports'] = len(ports) * len(all_hosts)

        print(f"{Colors.BOLD}{Colors.MAGENTA}Advanced Port Scanner v2.0 - NetHawk{Colors.END}")
        print(f"{Colors.BOLD}{'='*50}{Colors.END}")
        print(f"Targets: {Colors.CYAN}{', '.join(all_hosts[:3])}{', ...' if len(all_hosts) > 3 else ''}{Colors.END}")
        print(f"Ports: {Colors.CYAN}{len(ports)} ports{Colors.END}")
        print(f"Threads: {Colors.CYAN}{max_threads}{Colors.END}")
        print(f"Stealth Mode: {Colors.CYAN}{'Enabled' if self.stealth else 'Disabled'}{Colors.END}")
        print(f"Started: {Colors.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        print(f"{Colors.BOLD}{'='*50}{Colors.END}\n")
        
        # Scan each host
        for host in all_hosts:
            result = self.scan_host(host, ports, max_threads)
            if result:
                self.results[host] = result

        self.scan_stats['end_time'] = time.time()
        self.print_summary()


def main():
    """Main entry point for CLI use"""
    parser = argparse.ArgumentParser(
        description="Advanced Port Scanner - NetHawk - Enterprise Network Reconnaissance Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("targets", help="Target(s): IP, hostname, or CIDR (comma-separated)")
    parser.add_argument("-p", "--ports", default="top100",
                        help="Ports: range (1-1000), list (22,80,443), or preset (top100/top1000/all)")
    parser.add_argument("-t", "--timeout", type=float, default=1.0,
                        help="Connection timeout in seconds (default: 1.0)")
    parser.add_argument("--threads", type=int, default=100,
                        help="Number of concurrent threads (default: 100)")
    parser.add_argument("--stealth", action="store_true",
                        help="Enable stealth mode (slower, random delays)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output (show closed/filtered ports)")
    parser.add_argument("--export", help="Export results (filename prefix)")
    parser.add_argument("--format", choices=['json', 'csv', 'xml'], default='json',
                        help="Export format (default: json)")
    parser.add_argument("--version", action="version", version="NetHawk Port Scanner v2.0.0")

    args = parser.parse_args()

    # Split and clean targets
    targets = [t.strip() for t in args.targets.split(',')]

    try:
        scanner = AdvancedPortScanner(
            targets=targets,
            timeout=args.timeout,
            stealth=args.stealth,
            verbose=args.verbose
        )
        scanner.run_scan(args.ports, args.threads)

        if args.export:
            scanner.export_results(args.export, args.format)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[INTERRUPTED]{Colors.END} Scan stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.END} {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()