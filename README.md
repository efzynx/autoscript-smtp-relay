# SMTP Relay Auto-Installation & Management Tool

Sebuah tool komprehensif untuk **menginstal, mengatur, dan mengelola SMTP relay dengan Postfix** secara otomatis, kini dibangun di atas arsitektur FastAPI yang modern dan berkinerja tinggi.

Aplikasi ini menyediakan **sistem otomatisasi instalasi yang mudah digunakan untuk pemula**, dengan **dua antarmuka fleksibel**—Web UI berbasis browser dan Terminal UI (TUI) yang kaya fitur—yang keduanya berinteraksi dengan server API inti yang sama, memastikan konsistensi dan kemudahan pengelolaan.

## 🏛️ Arsitektur Aplikasi

Aplikasi ini menggunakan model client-server yang sederhana namun kuat:

 - **Server Inti (main.py):** Sebuah aplikasi FastAPI tunggal yang bertindak
   sebagai otak. Server ini menangani semua logika backend, seperti
   konfigurasi Postfix otomatis, manajemen sender, dan monitoring log, yang
   semuanya diekspos melalui REST API.
   
 - **Klien:**
	 - **Web UI**: Dasbor web modern dan intuitif dengan wizard instalasi otomatis, disajikan langsung oleh server FastAPI.
	 - **Terminal UI (cli.py & smtp_start.py):** Antarmuka berbasis teks yang lengkap (menggunakan curses) dengan wizard instalasi otomatis, sebagai klien yang mengirimkan perintah ke Server Inti melalui panggilan HTTP.

## 🚀 Fitur Utama

 - **Auto-Instalasi Pintar:** Sistem instalasi otomatis yang mendeteksi OS, menginstal dependensi, mengonfigurasi Postfix, dan memulai layanan dengan satu klik.
 - **Wizard Instalasi:** Antarmuka panduan langkah-demi-langkah untuk pengguna pemula, tersedia di Web UI dan TUI.
 - **Antarmuka Ganda, Satu Backend:** Kelola sistem Anda melalui Web UI grafis atau CLI yang praktis, dengan semua perubahan terpusat di server API.
 - **Server Terpadu:** Satu aplikasi FastAPI menangani permintaan API dan menyajikan antarmuka web, menyederhanakan deployment dan mengurangi kompleksitas.
 - **Manajemen Multi-Provider:** Konfigurasi otomatis untuk Gmail, Outlook, SendGrid, AWS SES, dan SMTP kustom.
 - **Manajemen SASL Menyeluruh:** Konfigurasikan detail otentikasi SMTP (relay host, username, password) dengan mudah baik melalui form di Web UI maupun menu di CLI.
 - **Manajemen Sender & Monitoring:** Tambah/edit/hapus sender, kirim email uji coba, dan pantau antrean serta log email secara real-time dari kedua antarmuka.
 - **Sistem Backup & Pemulihan:** Otomatis mencadangkan konfigurasi sebelum perubahan dan menyediakan fitur uninstall lengkap.
 - **Pengujian & Edukasi:** Cocok untuk pembelajaran dan pengujian SMTP relay dengan tampilan yang ramah pemula.

## 📋 Persyaratan

**Persyaratan Umum:**

 - Python 3.8+
 - Sistem Linux (Ubuntu, Debian, CentOS, RHEL, Fedora, Arch, dst.)
 - Akses `sudo` untuk konfigurasi Postfix
 - Postfix & Mailutils (akan diinstal secara otomatis jika belum ada)

## 🛠️ Instalasi dan Penggunaan

Pertama, kloning repositori ini:

    git clone https://github.com/efzynx/autoscript-smtp-relay.git
    
    cd autoscript-smtp-relay

**Instalasi Dependensi:**

    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt

**Jalankan Menu Utama:**
Gunakan skrip main_menu.py untuk memilih mode yang ingin Anda jalankan.

    python3 main_menu.py

Anda akan diberi pilihan:

 - **Jalankan Server (Web UI & API):** Ini akan memulai server Uvicorn. Setelah itu, Anda bisa membuka Web UI di `http://localhost:8000` untuk menggunakan wizard instalasi otomatis.
 - **Jalankan Mode CLI (Terminal):** Ini akan menjalankan smtp_start.py. Pastikan server sudah berjalan di terminal lain agar CLI dapat terhubung.

**Proses Instalasi Otomatis:**

1. Akses Web UI di `http://localhost:8000` atau gunakan TUI
2. Gunakan tombol "Install SMTP Relay" untuk membuka wizard instalasi
3. Ikuti langkah-langkah wizard:
   - Verifikasi informasi sistem Anda
   - Pilih provider email (Gmail, Outlook, SendGrid, AWS SES, atau kustom)
   - Masukkan kredensial SMTP Anda
   - Verifikasi konfigurasi dan mulai instalasi
4. Sistem akan otomatis:
   - Memeriksa kompatibilitas sistem
   - Menginstal semua dependensi yang diperlukan
   - Mengonfigurasi Postfix sesuai pengaturan Anda
   - Memulai dan mengaktifkan servis yang diperlukan
   - Memverifikasi instalasi berhasil

## 🔐 Catatan Keamanan

 - Pastikan akses ke Web UI di port 8000 diamankan jika Anda
   menjalankannya di server publik.
 - Aplikasi ini memerlukan akses sudo untuk memodifikasi file
   konfigurasi Postfix. Jalankan dengan hati-hati.
 - Kredensial SMTP disimpan secara lokal dan seharusnya hanya diakses oleh pengguna yang sah.
 - Gunakan App Password (bukan password utama) untuk layanan seperti Gmail.

## 🤝 Berkontribusi

Kontribusi sangat kami harapkan! Silakan buat Pull Request. Untuk perubahan besar, mohon buka issue terlebih dahulu untuk berdiskusi.