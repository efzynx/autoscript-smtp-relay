# SMTP Relay Setup Tool

Sebuah tool komprehensif untuk mengatur dan mengelola SMTP relay dengan Postfix, kini dibangun di atas arsitektur FastAPI yang modern dan berkinerja tinggi.

  

Aplikasi ini menyediakan dua antarmuka yang fleksibel—Web UI berbasis browser dan Terminal UI (TUI) yang kaya fitur—yang keduanya berinteraksi dengan server API inti yang sama, memastikan konsistensi dan kemudahan pengelolaan. Proyek ini dirancang untuk dapat dijalankan dengan mudah baik melalui Docker maupun secara lokal di terminal.

  

## 🏛️ Arsitektur Aplikasi

Aplikasi ini menggunakan model client-server yang sederhana namun kuat:

 - **Server Inti (main.py):** Sebuah aplikasi FastAPI tunggal yang bertindak
   sebagai otak. Server ini menangani semua logika backend, seperti
   konfigurasi Postfix, manajemen sender, dan monitoring log, yang
   semuanya diekspos melalui REST API.
   
 - **Klien:**
	 - **Web UI**: Dasbor web modern yang intuitif, disajikan langsung oleh server FastAPI.
	 - **Terminal UI (smtp_start.py):** Antarmuka berbasis teks yang lengkap (menggunakan curses) yang kini berfungsi sebagai klien, mengirimkan perintah ke Server Inti melalui panggilan HTTP.

  

## 🚀 Fitur Utama

 - **Antarmuka Ganda, Satu Backend:** Kelola sistem Anda melalui Web UI
   grafis atau CLI yang praktis, dengan semua perubahan terpusat di
   server API.
 - **Server Terpadu:** Tidak ada lagi server terpisah. Satu aplikasi FastAPI
   menangani permintaan API dan menyajikan antarmuka web,
   menyederhanakan deployment dan mengurangi kompleksitas.
 - **Deployment Fleksibel:**
	 - **Docker (Rekomendasi):** Jalankan seluruh aplikasi dalam satu kontainer terisolasi dengan satu perintah docker compose up.
	 - **Lokal:** Jalankan server dan klien secara langsung di terminal Anda menggunakan Python untuk kemudahan development dan debugging.
 - **Manajemen SASL Menyeluruh:** Konfigurasikan detail otentikasi SMTP
   (relay host, username, password) dengan mudah baik melalui form di
   Web UI maupun menu di CLI.
 - **Manajemen Sender & Monitoring:** Tambah/edit/hapus sender, kirim email
   uji coba, dan pantau antrean serta log email secara real-time dari
   kedua antarmuka.

  

## 📋 Persyaratan

**Untuk Menjalankan dengan Docker:**
 - Docker
 - Docker Compose

**Untuk Menjalankan Lokal (Tanpa Docker):**

 - Python 3.8+
 - Postfix & Mailutils (sudah terinstal di sistem Anda)
 - Akses `sudo` untuk konfigurasi Postfix

  

## 🛠️ Instalasi dan Penggunaan

Pertama, kloning repositori ini:

    git clone https://github.com/efzynx/autoscript-smtp-relay.git
    
    cd autoscript-smtp-relay

**Metode 1: Menjalankan dengan Docker (Direkomendasikan)**

Ini adalah cara termudah dan terbersih untuk menjalankan aplikasi.

**1. Jalankan Server:**

Gunakan Docker Compose untuk membangun image dan menjalankan kontainer di latar belakang.

    sudo docker compose up --build -d

**2. Akses Web UI:**

Buka browser Anda dan kunjungi:

    http://localhost:8000

**3. Akses Terminal UI (CLI):**

Buka terminal baru dan jalankan perintah berikut untuk masuk ke mode CLI di dalam kontainer yang sedang berjalan:

    sudo docker compose exec app python3 smtp_start.py

Menu CLI yang lengkap akan muncul di terminal Anda.

**Metode 2: Menjalankan Lokal (Tanpa Docker)**

Gunakan metode ini untuk development atau jika Anda tidak ingin menggunakan Docker.

**1. Instal Dependensi Python:**

    sudo pip3 install -r requirements.txt

**2. Jalankan Menu Utama:**
Gunakan skrip main_menu.py untuk memilih mode yang ingin Anda jalankan.

    python3 main_menu.py

Anda akan diberi pilihan:

 - **Jalankan Server (Web UI & API):** Ini akan memulai server Uvicorn. Setelah itu, Anda bisa membuka Web UI di `http://localhost:8000`.
 - **Jalankan Mode CLI (Terminal):** Ini akan menjalankan smtp_start.py. Pastikan server sudah berjalan di terminal lain agar CLI dapat
   terhubung.

  

## 🔐 Catatan Keamanan

 - Pastikan akses ke Web UI di port 8000 diamankan jika Anda
   menjalankannya di server publik.
 - Aplikasi ini memerlukan akses sudo untuk memodifikasi file
   konfigurasi Postfix. Jalankan dengan hati-hati.

## 🤝 Berkontribusi

Kontribusi sangat kami harapkan! Silakan buat Pull Request. Untuk perubahan besar, mohon buka issue terlebih dahulu untuk berdiskusi.

