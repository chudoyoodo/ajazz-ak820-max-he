import argparse
import hid

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x80b1

def set_deadzone(top_mm: float, bottom_mm: float, enable: bool):
    top_val = int(round(top_mm * 100)) & 0xff
    bot_val = int(round(bottom_mm * 100)) & 0xff
    en_flag = 0x01 if enable else 0x00

    packet = [
        0xaa, 0x21, 0x38, 0x00, 0x00, 0x00, 0x01, 0x00,
        0x00, 0x00, 0x00, 0x05, 0x00, 0x06, 0x00, 0x00,
        top_val, bot_val, 0x00, en_flag, 0x00, 0x00, 0x01
    ]
    packet += [0x00] * (64 - len(packet))

    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    if not devices:
        print("Ошибка: Клавиатура не найдена!")
        return

    for d in devices:
        try:
            dev = hid.device()
            dev.open_path(d['path'])
            dev.write([0x00] + packet)
            dev.close()
        except Exception:
            pass

    print(f"Dead Zone: {'ON' if enable else 'OFF'}, Top={top_mm}mm (0x{top_val:02x}), Bottom={bottom_mm}mm (0x{bot_val:02x})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Настройка Dead Zone для Ajazz AK820 Max HE")
    parser.add_argument("--top", type=float, default=0.30, help="Top Dead Zone в мм (по умолчанию 0.30)")
    parser.add_argument("--bottom", type=float, default=0.30, help="Bottom Dead Zone в мм (по умолчанию 0.30)")
    parser.add_argument("--enable", type=int, default=1, choices=[0, 1], help="1 — вкл, 0 — выкл")
    args = parser.parse_args()

    set_deadzone(args.top, args.bottom, bool(args.enable))
