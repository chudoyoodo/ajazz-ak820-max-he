import argparse
import hid

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x80b1

def set_color(power, r, g, b):
    packet = [
        0xaa, 0x23, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00,
        power, r, g, b, 0xff,
        0x00, 0x00, 0x00, 0x00, 0x05, 0x03, 0x00, 0x00, 0x00,
        0xaa, 0x55
    ] + [0x00] * 40

    for device_dict in hid.enumerate(VENDOR_ID, PRODUCT_ID):
        try:
            device = hid.device()
            device.open_path(device_dict['path'])
            device.write([0x00] + packet)
            device.close()
        except Exception:
            pass
    print(f"Цвет установлен: Power={power}, R={r:02x}, G={g:02x}, B={b:02x}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление подсветкой Ajazz AK820 Max HE")
    parser.add_argument("-p", "--power", type=int, default=1, choices=[0, 1], help="1 - вкл, 0 - выкл")
    parser.add_argument("-r", "--red", type=lambda x: int(x, 0), default=0xff, help="Красный (0-255)")
    parser.add_argument("-g", "--green", type=lambda x: int(x, 0), default=0x00, help="Зеленый (0-255)")
    parser.add_argument("-b", "--blue", type=lambda x: int(x, 0), default=0x00, help="Синий (0-255)")

    args = parser.parse_args()
    set_color(args.power, args.red, args.green, args.blue)
