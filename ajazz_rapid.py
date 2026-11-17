import argparse
import hid
import time

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x80b1

def set_switch_params(trigger_mm: float, press_mm: float, release_mm: float, enable_ft: bool, full_ft: bool):
    t_val = int(round(trigger_mm * 100))
    p_val = int(round(press_mm * 100)) if enable_ft else 0
    r_val = int(round(release_mm * 100)) if enable_ft else 0
    full_flag = 0x01 if (enable_ft and full_ft) else 0x00

    block = [
        0x03, full_flag,
        t_val & 0xff, (t_val >> 8) & 0xff,
        p_val & 0xff, (p_val >> 8) & 0xff,
        r_val & 0xff, (r_val >> 8) & 0xff,
    ]

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

            init_packet = [0xaa, 0x27, 0x10, 0xf0, 0x03, 0x00, 0x01, 0x00] + [0x00] * 56
            device.write([0x00] + init_packet)
            time.sleep(0.02)

            for off_low, off_high in offsets:
                packet = [0xaa, 0x27, 0x38, off_low, off_high, 0x00, 0x00, 0x00] + block * 7
                device.write([0x00] + packet[:64])
                time.sleep(0.01)

            device.close()
        except Exception:
            pass

    print(f"Применено: Trigger={trigger_mm}mm, FT={'ON' if enable_ft else 'OFF'}, Full_FT={'ON' if full_flag else 'OFF'}, Press={press_mm if enable_ft else 0}mm, Release={release_mm if enable_ft else 0}mm")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление магнитными свитчами Ajazz AK820 Max HE")
    parser.add_argument("--trigger", type=float, default=0.20, help="Trigger Distance в мм")
    parser.add_argument("--press", type=float, default=0.30, help="Press Sensitivity в мм")
    parser.add_argument("--release", type=float, default=0.16, help="Release Sensitivity в мм")
    parser.add_argument("--ft", type=int, default=1, choices=[0, 1], help="Fast Trigger: 1 (вкл) или 0 (выкл)")
    parser.add_argument("--full", type=int, default=0, choices=[0, 1], help="Full Distance FT: 1 (вкл) или 0 (выкл)")
    args = parser.parse_args()

    set_switch_params(args.trigger, args.press, args.release, bool(args.ft), bool(args.full))
