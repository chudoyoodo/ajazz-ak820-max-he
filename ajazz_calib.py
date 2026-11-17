import argparse
import hid
import time

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x80b1

def send_cmd(cmd_bytes):
    packet = cmd_bytes + [0x00] * (64 - len(cmd_bytes))
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    if not devices:
        print("Ошибка: Клавиатура не найдена!")
        return False
    for d in devices:
        try:
            dev = hid.device()
            dev.open_path(d['path'])
            dev.write([0x00] + packet)
            dev.close()
        except Exception:
            pass
    return True

def run_calibration(duration: int, clear_first: bool):
    print("Переводим клавиатуру в режим калибровки...")
    if not send_cmd([0xaa, 0x64]):
        return
    time.sleep(0.2)

    if clear_first:
        print("Сбрасываем старую калибровку (Clear)...")
        send_cmd([0xaa, 0x0f, 0x05])
        time.sleep(0.2)

    print(f"\n>>> КАЛИБРОВКА АКТИВНА ({duration} сек.) <<<")
    print("Клавиатура временно отключена от ОС. Прожмите до упора нужные клавиши!")
    
    for remaining in range(duration, 0, -1):
        print(f"Осталось секунд: {remaining:2d}...", end="\r")
        time.sleep(1)

    print("\nСохраняем калибровку и возвращаем клавиатуру в рабочий режим...")
    send_cmd([0xaa, 0x65])
    print("Готово! Клавиатура снова работает в штатном режиме.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Оффлайн-калибровка Ajazz AK820 Max HE")
    parser.add_argument("-t", "--time", type=int, default=15, help="Время на калибровку в секундах (по умолчанию 15)")
    parser.add_argument("--clear", action="store_true", help="Сбросить текущую калибровку перед началом")
    args = parser.parse_args()

    run_calibration(args.time, args.clear)
