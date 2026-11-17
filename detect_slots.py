import hid
import time

dev = None
for d in hid.enumerate(0x0c45, 0x80b1):
    if d.get("interface_number") == 2:
        dev = hid.device()
        dev.open_path(d["path"])
        dev.set_nonblocking(True)
        break

if not dev:
    print("Клавиатура не найдена!")
    exit(1)

dev.write([0x00, 0xaa, 0x64] + [0x00] * 62)
print("Режим калибровки активен. Нажимайте серые клавиши по очереди.")
print("Чтобы завершить и сохранить результат — нажмите [Esc] на клавиатуре.\n")

seen = []
try:
    while True:
        while True:
            data = dev.read(64)
            if not data:
                break
            if len(data) >= 10 and data == 0x55 and data == 0xfb:
                slot = data
                top_adc = data | (data << 8)
                cur_adc = data | (data << 8)
                if (top_adc - cur_adc) > 400:
                    if slot == 0:
                        raise StopIteration
                    if slot not in seen:
                        seen.append(slot)
                        print(f"\033[2K\rПоймано ({len(seen)}): {seen}", end="", flush=True)
        time.sleep(0.01)
except (StopIteration, KeyboardInterrupt):
    pass
finally:
    dev.write([0x00, 0xaa, 0x65] + [0x00] * 62)
    dev.close()
    print(f"\n\nГотово! Итоговый список слотов:\n{seen}")
