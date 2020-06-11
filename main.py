from class_cnc import CNC
import queue
import threading
from time import sleep
from class_rectangle import Point

# Function of input in thread
def read_kbd_input(__input_queue):
    while True:
        # Receive keyboard input from user.
        try:
            input_str = input()
            __input_queue.put(input_str)
        except:
            continue
        sleep(0.01)

if __name__ == '__main__':
    cnc = CNC(x_max=45, y_max=35, safe_travel=2, com_port='COM8', speed=115200)
    # cnc.rect.get_point(Point(0, 0)).deviation = 0.01
    # cnc.rect.get_point(Point(55, 0)).deviation = 0.26
    # cnc.rect.get_point(Point(0, 70)).deviation = 10.78
    # cnc.rect.get_point(Point(55, 70)).deviation = 11.13

    if cnc.initialized:
        # Start keyboart queue thread
        input_queue = queue.Queue()
        inputThread = threading.Thread(target=read_kbd_input, args=(input_queue,), daemon=True)
        inputThread.start()

        while True:
            if (input_queue.qsize() > 0):
                input_str = input_queue.get()
                answer = cnc.parse_command(input_str)
                if answer is not None:
                    print(answer)
            sleep(0.01)