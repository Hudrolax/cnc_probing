# coding=utf-8
import serial

class SerialCNC:
    def __init__(self, com_port, speed:int = 115200):
        self._com_port = com_port
        self._speed = speed
        self._initialized = False
        print(f'try to open port {self._com_port}')
        try:
            self._serial = serial.Serial(com_port, self._speed)
            self._serial.reset_output_buffer()
            self._serial.reset_input_buffer()
            self._serial.baudrate = self._speed
            self._serial.timeout = 5
            self._serial.write_timeout = 5
        except:
            raise Exception(f'Connot open the port {self._serial}')


    staticmethod
    def clear_str(str_):
        str_ = str(str_)
        str_ = str_.replace("\\r", '')
        str_ = str_.replace("\\n", '')
        str_ = str_.replace("b'", '')
        str_ = str_.replace("'", '')
        return str_

    def close(self):
        self._serial.close()

    def read(self):
        answer = ''
        try:
            answer = str(self._serial.readline())
        except:
            print('Read error from port ' + self._serial)
            return answer
        answer = SerialCNC.clear_str(answer)
        return answer

    def send(self, data:str):
        self._serial.write(bytes(data+'\r\n','utf-8'))

if __name__ == '__main__':
    com_port = SerialCNC('COM8', 115200)
    com_port.send('G0 X5 F1500')
    answer = com_port.read()
    print('answer: ' + answer)
    com_port.close()