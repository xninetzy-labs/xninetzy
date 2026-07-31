# HEBAT Debug Guide

Tujuan: debug login HEBAT secara aman tanpa membocorkan credential.

Command:
• `/hebat-debug`

Output:
• env username terbaca/kosong
• env password tersedia/kosong
• login URL
• HTTP status
• redirect chain ada/tidak
• token ditemukan ya/tidak
• cookie session ada/tidak
• login success indicator
• dugaan masalah

Tidak ditampilkan:
• password
• cookie value
• token value
• sesskey
• session id

Batasan: membutuhkan Playwright dan akses jaringan ke Moodle.
