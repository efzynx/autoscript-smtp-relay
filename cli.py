#!/usr/bin/env python3
"""
CLI untuk berinteraksi dengan SMTP Relay API.
"""
import requests
import json

# URL tempat API server berjalan
API_BASE_URL = "http://localhost:8000/api"

def print_header(title):
    print("\n" + "="*40)
    print(f" {title}")
    print("="*40)

def get_senders():
    print_header("Daftar Sender Saat Ini")
    try:
        response = requests.get(f"{API_BASE_URL}/senders")
        response.raise_for_status()
        senders = response.json()
        if not senders:
            print("Belum ada sender yang dikonfigurasi.")
        else:
            for i, sender in enumerate(senders):
                print(f"{i+1}. {sender['name']} <{sender['email']}>")
    except requests.exceptions.RequestException as e:
        print(f"Error: Tidak dapat terhubung ke API server. Pastikan server berjalan.\n{e}")

def add_sender():
    print_header("Tambah Sender Baru")
    try:
        name = input("Masukkan nama sender: ")
        email = input("Masukkan email sender: ")
        payload = {"name": name, "email": email}
        response = requests.post(f"{API_BASE_URL}/senders", json=payload)
        response.raise_for_status()
        print("\n✅ Sender berhasil ditambahkan!")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Gagal menambahkan sender: {e.response.json() if e.response else e}")

def configure_sasl():
    print_header("Konfigurasi SASL (SMTP Relay)")
    try:
        relay_host = input("Masukkan Relay Host (contoh: smtp.example.com:587): ")
        username = input("Masukkan Username SMTP: ")
        password = input("Masukkan Password SMTP: ")
        
        payload = {
            "relay_host": relay_host,
            "username": username,
            "password": password
        }
        
        print("\nMengirim konfigurasi ke server...")
        response = requests.post(f"{API_BASE_URL}/configure_sasl", json=payload)
        response.raise_for_status()
        print(f"\n✅ Berhasil! Pesan dari server: {response.json().get('message')}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Gagal mengkonfigurasi SASL: {e.response.json() if e.response else e}")

def main_menu():
    while True:
        print_header("SMTP Relay CLI Menu")
        print("1. Lihat Daftar Sender")
        print("2. Tambah Sender Baru")
        print("3. Konfigurasi SASL (SMTP Relay)")
        print("4. Keluar")
        choice = input("Pilih opsi [1-4]: ")

        if choice == '1':
            get_senders()
        elif choice == '2':
            add_sender()
        elif choice == '3':
            configure_sasl()
        elif choice == '4':
            break
        else:
            print("Pilihan tidak valid, silakan coba lagi.")
        
        input("\nTekan Enter untuk kembali ke menu...")

if __name__ == "__main__":
    main_menu()

