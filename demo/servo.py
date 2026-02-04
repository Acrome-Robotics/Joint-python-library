import serial
import time

class ServoSurucu:
    def __init__(self, port, baud_rate=9600):
        """
        Servo bağlantısını başlatır.
        port: 'COM3', '/dev/ttyUSB0' vb.
        """
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.baglanti_kur()

    def baglanti_kur(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"[{self.port}] Bağlantı başarılı. Arduino başlatılıyor...")
            # Arduino resetlendiğinde bootloader'ın açılması için bekleme süresi
            time.sleep(2) 
            print("Servo sistemi hazır.")
        except serial.SerialException as e:
            print(f"HATA: Port açılamadı -> {e}")

    def aci_gonder(self, aci):
        """
        Servoya belirtilen açıyı gönderir.
        aci: 0-180 arası tam sayı
        """
        if self.ser and self.ser.is_open:
            try:
                # Güvenlik ve tip kontrolü
                aci = int(aci)
                if 0 <= aci <= 180:
                    komut = f"{aci}\n"
                    self.ser.write(komut.encode('utf-8'))
                    # Gereksiz buffer şişmesini önlemek için feedback okuma (opsiyonel)
                    # self.ser.reset_input_buffer() 
                    return True
                else:
                    print(f"UYARI: Açı 0-180 aralığında olmalı. Girilen: {aci}")
                    return False
            except ValueError:
                print("HATA: Açı sayısal bir değer olmalı.")
                return False
            except Exception as e:
                print(f"İletişim Hatası: {e}")
                return False
        else:
            print("HATA: Seri port bağlı değil.")
            return False

    def kapat(self):
        """Seri portu güvenli şekilde kapatır."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Bağlantı kapatıldı.")