import serial
import time

# --- AYARLAR ---
# Windows için 'COM3', 'COM4' vb. 
# Mac/Linux için '/dev/ttyUSB0' vb.
arduino_port = 'COM9'  # BURAYI KENDİ PORTUNA GÖRE DEĞİŞTİR
baud_rate = 9600

try:
    # Seri portu açıyoruz
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"{arduino_port} uzerinden baglanti kuruldu.")
    
    # Arduino resetlendiğinde bootloader'ın açılması için 2 saniye beklemeliyiz
    # Yoksa ilk gönderdiğin veri kaybolabilir.
    time.sleep(2) 
    print("Sistem hazir. Cikmak icin 'q' veya 'exit' yazin.")

    while True:
        user_input = input("Aci girin (0-180): ")

        # Çıkış kontrolü
        if user_input.lower() in ['q', 'exit']:
            print("Program kapatiliyor...")
            break

        # Sadece sayı girildiğinden emin olalım
        if user_input.isdigit():
            angle = int(user_input)
            
            if 0 <= angle <= 180:
                # Veriyi string'e çevir, sonuna \n ekle ve byte olarak gönder
                command = f"{angle}\n"
                ser.write(command.encode('utf-8'))
                
                # Arduino'dan gelen cevabı (feedback) okuyalım (Opsiyonel)
                # Arduino kodunda Serial.print satırları varsa buradan okuruz
                time.sleep(0.05) # Cevabın gelmesi için minik bekleme
                while ser.in_waiting:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print(f"Arduino Cevabi: {response}")
            else:
                print("Lutfen 0 ile 180 arasinda bir deger girin.")
        else:
            print("Gecersiz giris. Sayi girin.")

except serial.SerialException:
    print(f"HATA: {arduino_port} portuna baglanilamadi. Portu ve kabloyu kontrol et.")
except Exception as e:
    print(f"Bir hata olustu: {e}")
finally:
    # Portu her durumda güvenli kapat
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Port kapatildi.")