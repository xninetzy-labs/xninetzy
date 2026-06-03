# Deep Research: Sistem Informasi Perpustakaan Berbasis Web

## 1. Konsep Dasar
- Definisi Sistem Informasi: kumpulan komponen (hardware, software, data, manusia, prosedur) yang mengelola informasi
- SI Berbasis Web: akses via browser, arsitektur client-server, pakai HTTP/HTTPS
- Studi kasus perpustakaan: kelola buku, anggota, peminjaman, pengembalian, denda

## 2. Arsitektur & Workflow
- Aktor: Admin, Pustakawan, Anggota
- Alur utama: Login → Cari buku → Pinjam → Kembali → Denda (jika telat)
- DFD Context: entitas luar (Anggota, Admin) ↔ Sistem Perpustakaan
- DFD Level 0: proses utama — Kelola Buku, Kelola Anggota, Transaksi Pinjam, Transaksi Kembali, Hitung Denda

## 3. CDM & PDM
- Entity: Buku (id, judul, penulis, isbn, stok), Anggota (id, nama, alamat), Peminjaman (id, tgl_pinjam, tgl_kembali), Pengembalian (id, tgl_dikembalikan, denda)
- Relasi: Anggota 1—M Peminjaman, Buku 1—M Peminjaman
- PDM: konversi ke tabel MySQL dengan foreign key

## 4. UML Diagrams
- Use Case: Login, Cari Buku, Pinjam Buku, Kembalikan Buku, Kelola Data Buku, Kelola Anggota, Lihat Laporan
- Activity Diagram: flowchart tiap use case
- Class Diagram: class Buku, Anggota, Peminjaman, Pengembalian + method
- Sequence Diagram: interaksi objek per skenario (pinjam & kembali)

## 5. UI/UX & Implementasi
- Wireframe: Halaman login, dashboard admin, daftar buku, form pinjam
- Teknologi: HTML/CSS/JS + PHP + MySQL
- Struktur folder MVC sederhana: /controllers, /models, /views, /assets

## 6. Tools Rekomendasi
- Diagram: Draw.io, Lucidchart, StarUML
- UI: Figma (free)
- Koding: VS Code, XAMPP/Laragon
- Referensi: slide kampus, jurnal SI perpustakaan

## 7. Plan 8 Minggu
| Minggu | Bab | Fokus |
|--------|-----|-------|
| 1 | 1+2 | Pengantar & Deskripsi Sistem |
| 2 | 3 | DFD (Context + Level 0/1) |
| 3 | 4 | CDM & PDM |
| 4 | 5 | Use Case Diagram |
| 5 | 6+7 | Activity & Class Diagram |
| 6 | 8 | Sequence Diagram |
| 7 | 9 | UI/UX (Wireframe) |
| 8 | 10 | Implementasi + Finalisasi |

## 8. Referensi Pencarian YouTube
- "DFD context diagram perpustakaan draw.io"
- "CDM PDM database perpustakaan MySQL"
- "Use case activity class sequence diagram UML perpustakaan"
- "Figma wireframe sistem perpustakaan"
- "Membuat aplikasi perpustakaan PHP MySQL"