# PROJE 7 – Eşzamanlı Parçalı Dosya İndirme Yöneticisi

## Amaç
Büyük dosyaları HTTP Range başlıkları kullanarak eşzamanlı indirmek ve parçaları tek dosyada birleştirmek.

## Kullanılan Teknolojiler
- Python
- asyncio
- httpx
- Flask
- HTML, CSS ve JavaScript

## Çalışma Algoritması
1. HEAD isteğiyle dosya boyutu ve Range desteği kontrol edilir.
2. Dosya dört bayt aralığına bölünür.
3. Dört işçi, HTTP Range istekleriyle parçaları eşzamanlı indirir.
4. Her işçi seek() yöntemiyle verileri hedef dosyadaki doğru konuma yazar.
5. Parçaların uzunlukları ve toplam dosya boyutu kontrol edilir.

## Görsel Arayüz
Flask tabanlı web arayüzünde indirme başlatılabilir ve dört parçanın tamamlanma durumları görüntülenebilir.

## Kurulum
pip install -r requirements.txt

## Çalıştırma
python main.py

Görsel arayüz için:
python app.py

Tarayıcı adresi:
http://127.0.0.1:5000

## Sonuç
1.048.576 baytlık test dosyası dört parça halinde başarıyla indirilmiş ve tek dosyada birleştirilmiştir.

Not: İlerleme çubukları anlık indirme yüzdesini değil, parçaların tamamlanma durumunu gösterir.