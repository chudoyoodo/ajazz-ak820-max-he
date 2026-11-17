import argparse
import hid
import time

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x80b1

def set_trigger_distance_full(mm: float):
    val = int(round(mm * 100))
    low_byte = val & 0xff
    high_byte = (val >> 8) & 0xff

    print(f"Установка Trigger Distance: {mm} мм (значение: {val}, hex: 0x{low_byte:02x}) для всей клавиатуры...")

    # Базовый блок клавиш из логов
    block = [0x03, 0x01, low_byte, high_byte, 0x1e, 0x00, 0x10, 0x00]

    # Список смещений (байты на позициях 3 и 4), которые шлет софт при Select All
    # Из ваших логов: 0x0000, 0x0038, 0x0070, 0x00a8, 0x00e0, 0x0118, 0x0150, 0x0188, 0x01c0, 0x01f8, ...
    offsets = [
        (0x00, 0x00), (0x38, 0x00), (0x70, 0x00), (0xa8, 0x00), (0xe0, 0x00),
        (0x18, 0x01), (0x50, 0x01), (0x88, 0x01), (0xc0, 0x01), (0xf8, 0x01),
        (0x30, 0x02), (0x68, 0x02), (0xa0, 0x02), (0xd8, 0x02), (0x10, 0x03),
        (0x48, 0x03), (0x80, 0x03), (0xb8, 0x03)
    ]

    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    if not devices:
        print("Ошибка: Клавиатура не найдена!")
        return

    for device_dict in devices:
        try:
            device = hid.device()
            device.open_path(device_dict['path'])

            # 1. Сначала сервисный пакет инициализации
            init_packet = [0xaa, 0x27, 0x10, 0xf0, 0x03, 0x00, 0x01, 0x00] + [0x00] * 56
            device.write([0x00] + init_packet)
            time.sleep(0.02)

            # 2. Шлем всю последовательность блоков со смещениями
            for off_low, off_high in offsets:
                packet = [
                    0xaa, 0x27, 0x38, off_low, off_high, 0x00, 0x00, 0x00
                ] + block * 6
                
                while len(packet) < 64:
                    packet.append(0x00)

                device.write([0x00] + packet)
                time.sleep(0.01) # небольшая пауза между пакетами, как в браузере

            device.close()
            print(f"Пакеты успешно отправлены на интерфейс: {device_dict['path']}")
        except Exception as e:
            print(f"Ошибка при записи: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Полный скрипт с учетом Select All для Ajazz AK820 Max HE")
    parser.add_argument("mm", type=float, default=0.20, help="Дистанция в мм (например, 0.1, 0.2, 0.5)")
    args = parser.parse_args()
    
    set_trigger_distance_full(args.mm)
