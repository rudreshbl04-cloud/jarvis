"""
SSL / TLS Certificate Generator for JARVIS LAN Phone Access.
Generates SAN-enabled certificates for localhost and LAN IP to enable secure
WebRTC microphone and camera access on mobile devices.
"""

import os
import sys
import socket
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith('127.'):
            return ip
    except Exception:
        pass
    return '127.0.0.1'

def generate_cert_cryptography(lan_ip, cert_path, key_path):
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        import ipaddress

        print("Generating RSA key pair...")
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Jarvis Local Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"Jarvis ({lan_ip})"),
        ])

        san_list = [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
        if lan_ip != "127.0.0.1":
            san_list.append(x509.IPAddress(ipaddress.IPv4Address(lan_ip)))

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        ).sign(key, hashes.SHA256())

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"[OK] Certificate created: {cert_path}")
        print(f"[OK] Private key created: {key_path}")
        return True
    except ImportError:
        print("[INFO] 'cryptography' package not found. Attempting PowerShell generator...")
        return False
    except Exception as e:
        print(f"[FAIL] Error generating cert via cryptography: {e}")
        return False

def generate_cert_powershell(lan_ip, cert_path, key_path):
    ps_cmd = f"""
    $cert = New-SelfSignedCertificate -DnsName "localhost", "{lan_ip}" -CertStoreLocation "Cert:\\CurrentUser\\My" -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(1)
    $pwd = ConvertTo-SecureString -String "jarvis_temp_pass" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath "{REPO_ROOT}\\temp_cert.pfx" -Password $pwd
    """
    try:
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
        if res.returncode == 0:
            print("[OK] Self-signed certificate generated via PowerShell.")
            return True
        else:
            print(f"[WARN] PowerShell certificate generation error: {res.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] PowerShell invocation failed: {e}")
        return False

def main():
    lan_ip = get_lan_ip()
    print("=" * 60)
    print("  JARVIS SSL / TLS CONFIGURATION FOR LAN PHONE CLIENT")
    print("=" * 60)
    print(f"Detected LAN IP: {lan_ip}")

    cert_path = REPO_ROOT / "cert.pem"
    key_path = REPO_ROOT / "key.pem"

    ok = generate_cert_cryptography(lan_ip, cert_path, key_path)
    if not ok:
        ok = generate_cert_powershell(lan_ip, cert_path, key_path)

    print("\nPHONE TRUST & WEBRTC INSTRUCTIONS:")
    print("-" * 60)
    print("1. To use phone microphone and camera over Wi-Fi, browsers require HTTPS.")
    print("2. When accessing https://<laptop-ip>:5443 for the first time:")
    print("   - Chrome/Safari will display 'Your connection is not private'.")
    print("   - Tap 'Advanced' -> 'Proceed to <ip> (unsafe)' or install cert.pem into phone certificates.")
    print("   - Grant microphone and camera access when prompted.")
    print("3. Alternatively, use the Android WebView wrapper in 'mobile/android' which handles")
    print("   local LAN SSL validation automatically without security degradation.")
    print("=" * 60)

if __name__ == "__main__":
    main()
