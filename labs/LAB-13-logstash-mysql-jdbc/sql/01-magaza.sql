-- Ornek magaza veritabani (sentetik). Ilk acilista MySQL container'i bu dosyayi calistirir.
SET NAMES utf8mb4;
-- Logstash'in kullanicisi yalniz okuyabilir: SELECT disinda yetkisi yok.
CREATE USER 'logstash_okuyucu'@'%' IDENTIFIED BY 'Okuyucu2026!';
GRANT SELECT ON magaza.* TO 'logstash_okuyucu'@'%';
CREATE TABLE musteriler (id INT PRIMARY KEY, ad VARCHAR(80) NOT NULL, il VARCHAR(40) NOT NULL);
CREATE TABLE urunler (id INT PRIMARY KEY, ad VARCHAR(80) NOT NULL, kategori VARCHAR(40) NOT NULL, fiyat DECIMAL(10,2) NOT NULL);
CREATE TABLE siparisler (
  id INT PRIMARY KEY,
  musteri_id INT NOT NULL,
  urun_id INT NOT NULL,
  adet INT NOT NULL,
  durum VARCHAR(20) NOT NULL,
  guncellendi TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  FOREIGN KEY (musteri_id) REFERENCES musteriler(id),
  FOREIGN KEY (urun_id) REFERENCES urunler(id)
);
INSERT INTO musteriler VALUES (1, 'Ağaoğlu Yapı', 'İstanbul'), (2, 'Şimşek Lojistik', 'Ankara'), (3, 'Öztürk Gıda', 'İzmir'), (4, 'Çınar Eğitim', 'Bursa'), (5, 'Güneş Enerji', 'Antalya'), (6, 'Yıldız Tekstil', 'İstanbul');
INSERT INTO urunler VALUES (1, 'Dizüstü Bilgisayar', 'Bilgisayar', 28499.90), (2, 'Kablosuz Kulaklık', 'Ses', 1299.50), (3, 'Akıllı Saat', 'Giyilebilir', 2199.00), (4, 'Ofis Sandalyesi', 'Mobilya', 4750.00), (5, 'Bluetooth Hoparlör', 'Ses', 899.90);
INSERT INTO siparisler VALUES
  (101, 1, 1, 1, 'hazırlanıyor', '2026-11-01 09:00:00.000'),
  (102, 6, 4, 4, 'teslim edildi', '2026-11-02 10:13:00.000'),
  (103, 5, 2, 3, 'kargoda', '2026-11-03 11:26:00.000'),
  (104, 4, 5, 2, 'hazırlanıyor', '2026-11-04 12:39:00.000'),
  (105, 3, 3, 1, 'teslim edildi', '2026-11-05 13:52:00.000'),
  (106, 2, 1, 4, 'kargoda', '2026-11-06 14:05:00.000'),
  (107, 1, 4, 3, 'hazırlanıyor', '2026-11-07 15:18:00.000'),
  (108, 6, 2, 2, 'teslim edildi', '2026-11-08 16:31:00.000'),
  (109, 5, 5, 1, 'kargoda', '2026-11-09 09:44:00.000'),
  (110, 4, 3, 4, 'hazırlanıyor', '2026-11-10 10:57:00.000'),
  (111, 3, 1, 3, 'teslim edildi', '2026-11-11 11:10:00.000'),
  (112, 2, 4, 2, 'kargoda', '2026-11-12 12:23:00.000'),
  (113, 1, 2, 1, 'hazırlanıyor', '2026-11-13 13:36:00.000'),
  (114, 6, 5, 4, 'teslim edildi', '2026-11-14 14:49:00.000'),
  (115, 5, 3, 3, 'kargoda', '2026-11-15 15:02:00.000'),
  (116, 4, 1, 2, 'hazırlanıyor', '2026-11-16 16:15:00.000'),
  (117, 3, 4, 1, 'teslim edildi', '2026-11-17 09:28:00.000'),
  (118, 2, 2, 4, 'kargoda', '2026-11-18 10:41:00.000'),
  (119, 1, 5, 3, 'hazırlanıyor', '2026-11-19 11:54:00.000'),
  (120, 6, 3, 2, 'teslim edildi', '2026-11-20 12:07:00.000');
