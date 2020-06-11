from class_serial import SerialCNC
from class_rectangle import Rectangle
from class_rectangle import Point
from prettytable import PrettyTable
import os.path

class Cmd:
    def __init__(self, cmd, x, y, z, f):
        self.cmd = cmd
        self.x = x
        self.y = y
        self.z = z
        self.f = f

    def __str__(self):
        print(f'{self.cmd} X{self.x} Y{self.y} Z{self.z} F{self.f}')

class CNC(SerialCNC):
    def __init__(self, x_max, y_max, safe_travel, com_port, speed:int = 115200):
        super().__init__(com_port, speed)
        self.rect = Rectangle(x_max, y_max)
        self._probing_speed = 5
        self._travel_speed = 1300
        self._safe_travel = safe_travel
        self.x = 0
        self.y = 0
        self.z = 0
        self.load_map_from_file()
        self.m114()
        self._initialized = True
        print(f'X{self.x} Y{self.y} Z{self.z}')

    @property
    def safe_travel(self):
        return self._safe_travel

    @safe_travel.setter
    def safe_travel(self, val):
        if isinstance(val, int) or isinstance(val, float):
            if val > 240:
                val = 240
            elif val < 0:
                val = 0
            self._safe_travel = val
        else:
            raise TypeError(f'safe_travel type error. Need int/float but got {type(val)}')

    @property
    def travel_speed(self):
        return self._travel_speed

    @travel_speed.setter
    def travel_speed(self, val):
        if val > 3000:
            val = 3000
        elif val < 100:
            val = 100
        self._travel_speed = val

    @property
    def initialized(self):
        return self._initialized

    @property
    def probing_speed(self):
        return self._probing_speed

    @probing_speed.setter
    def probing_speed(self, val):
        if val < 1 or val > 100:
            print(f'incorrect probing speed {val}')
        else:
            self._probing_speed = val

    def send_read(self, data:str):
        self._serial.write(bytes(data + '\r\n', 'utf-8'))
        while True:
            data = self.read()
            if data == 'ok':
                return data

    def pos(self):
        return f'X{self.x} Y{self.y} Z{self.z}'

    def m114(self):
        self.send('M114')
        while True:
            data = self.read()
            if data == 'ok':
                return
            elif data.startswith('echo:busy'):
                print(data)
            elif data.startswith('X:'):
                lines = data.split(' ')
                if len(lines) > 2:
                    self.x = float(lines[0].split(':')[1])
                    self.y = float(lines[1].split(':')[1])
                    self.z = float(lines[2].split(':')[1])
                else:
                    raise Exception('error parsing M114 answer')

    def probing(self):
        self.m114()
        if self.z > 100 or self.z < self.safe_travel:
            print(f'Z heigh ({self.z}) too much for probign. Set Z to heigh {self.safe_travel} - 100')
            return
        self.send_read(f'G38.4 Z-100 F{self._probing_speed}')
        self.m114()

    def go_to(self, x, y, z=None, f=None):
        if z is None:
            z = self.safe_travel
        _deviation = self.rect[x, y].deviation
        # print(f'go_to X{x} Y{x} deviation {_deviation}')
        if f is None:
            f = self.travel_speed
        return self.send_read(f'G0 X{x} Y{y} Z{z + _deviation} F{f}')

    def save_map_to_file(self):
        try:
            f = open('map.txt', 'w')
            for point in self.rect.points:
                f.write(f'{point.x} {point.y} {point.deviation}\n')
            f.close()
        except:
            print("can't save map to map.txt")

    def load_map_from_file(self):
        try:
            f = open('map.txt', 'r')
            content = f.readlines()
            for line in content:
                line = line.replace('\n', '')
                coord = line.split(' ')
                # print(coord)
                for point in self.rect.points:
                    if coord[0] == str(point.x) and coord[1] == str(point.y):
                        point.deviation = float(coord[2])
            f.close()
        except:
            print("can't load map from map.txt")

    def probe_from_rectangle(self):
        self.m114()
        if not (self.x == 0 and self.y == 0):
            print(f'Probign rom rect error: cnc is on in zero (X{self.x} Y{self.y})')
            return
        if self.z > 80 or self.z < self.safe_travel:
            print(f'Z heigh ({self.z}) is wrong for probign. Set Z to heigh {self.safe_travel} - 80')
            return
        print('probing...')
        self.probing()
        print('reset z-coord to 0')
        self.send_read('G92 Z0')
        print(f'go up to safe travel heigh ({self.safe_travel}mm)')
        self.send_read(f'G0 Z{self.safe_travel}')
        self.m114()
        print('start to rect probing')
        k = 1
        for point in self.rect.points:
            print(f'go to point ({point.x}, {point.y})')
            self.send_read(f'G0 X{point.x} Y{point.y} Z{self.safe_travel} F{self.travel_speed}')
            print(f'probing {k}/{self.rect.probe_net[0]*self.rect.probe_net[1]}')
            self.probing()
            point.deviation = self.z
            k += 1
        # save map to file
        self.save_map_to_file()
        print('End of probing!')
        print('Go to Zero')
        self.send_read(f'G0 X0 Y0 Z{self.safe_travel} F{self.travel_speed}')
        self.draw_deviation_map_table()
        return 'ok'

    def parse_g0(self, cmd, not_self = False):
        if cmd.lower().startswith('g0') or cmd.lower().startswith('g1'):
            if cmd.lower().startswith('g0'):
                cnc_cmd = 'G0'
            elif cmd.lower().startswith('g1'):
                cnc_cmd = 'G1'
            attr_list = cmd.split(' ')
            _x = None
            _y = None
            _z = None
            _f = None
            for attr in attr_list:
                if attr.lower().startswith('x'):
                    attr = attr.replace('X', '')
                    attr = attr.replace('x', '')
                    _x = float(attr)
                elif attr.lower().startswith('y'):
                    attr = attr.replace('Y', '')
                    attr = attr.replace('y', '')
                    _y = float(attr)
                elif attr.lower().startswith('z'):
                    attr = attr.replace('Z', '')
                    attr = attr.replace('z', '')
                    _z = float(attr)
                elif attr.lower().startswith('f'):
                    attr = attr.replace('F', '')
                    attr = attr.replace('f', '')
                    _f = float(attr)

            if not not_self:
                if _x is None:
                    _x = self.x
                if _y is None:
                    _y = self.y
                if _z is None:
                    _z = self.z
                if _f is None:
                    _f = self.travel_speed

            _cmd = Cmd(cnc_cmd,_x, _y, _z, _f)
            # print(_cmd)
            return _cmd
        return None

    def draw_deviation_map_table(self):
        table = PrettyTable()
        _field_names = ['X:Y']
        for x_probe_coord in self.rect.x_probe_points:
            _field_names.append(x_probe_coord)
        table.field_names = _field_names

        for y_probe_coord in reversed(self.rect.y_probe_points):
            _row = [y_probe_coord]
            for x_probe_coord in self.rect.x_probe_points:
                _row.append(self.rect.get_point(Point(x_probe_coord, y_probe_coord)).deviation)
            table.add_row(_row)
        print('***   Probing deviation   ***')
        print(table.get_string(title="Probing deviation"))

    def modify_file(self, file_name):
        try:
            if os.path.exists(file_name):
                x_max = 0
                y_max = 0
                x = 0
                y = 0
                z = 0
                f = open(file_name, 'r')
                f2 = open(f'out_{file_name}', 'w')
                content = f.readlines()
                for line in content:
                    _cmd = self.parse_g0(line, True)
                    if _cmd is not None:
                        if _cmd.x is not None:
                            x = _cmd.x
                        if _cmd.y is not None:
                            y = _cmd.y
                        if _cmd.z is not None:
                            z = _cmd.z
                        if x > x_max:
                            x_max = x
                        if y > y_max:
                            y_max = y
                        _dev = self.rect[x, y].deviation
                        new_line = f'{_cmd.cmd} X{x} Y{y} Z{round(z+_dev,4)} F{_cmd.f}'
                        f2.write(new_line+'\n')
                    else:
                        f2.write(line+'\n')
                f.close()
                f2.close()
                if x_max > self.rect.x_max:
                    print(f'WARNING!!!! In file {file_name} x_max is {x_max}, but x_man in rect is {self.rect.x_max}')
                if y_max > self.rect.y_max:
                    print(f'WARNING!!!! In file {file_name} y_max is {y_max}, but y_man in rect is {self.rect.y_max}')
            else:
                print(f'File {file_name} do not exist.')
        except:
            raise IOError

    def parse_command(self, cmd:str):
        if cmd == 'pos':
            self.m114()
            return self.pos()
        elif cmd == 'read': #читает ответ от принтера (для отладки)
            return self.read()
        elif cmd.startswith('send'): # отправляет команду напрямую на принтер без чтения ответа (для отладки)
            cmd = cmd.replace('send ','')
            self.send(cmd)
        elif cmd.startswith('go_to ') or cmd.startswith('goto '): # перемещение в пределах rect с коррекцией по deviation
            cmd = cmd.replace('goto ', '')
            cmd = cmd.replace('go_to ','')
            cmd = cmd.replace('G0 ', '')
            cmd = cmd.replace('g0 ', '')
            cmd = cmd.replace('G0', '')
            cmd = cmd.replace('g0', '')
            _cmd = self.parse_g0(f'G0 {cmd}')
            # print(coord)
            if _cmd.x > self.rect.x_max or _cmd.x < 0 or _cmd.y > self.rect.y_max or _cmd.y < 0:
                return 'coordinates is out of range of cnc.rect'
            return self.go_to(_cmd.x, _cmd.y, _cmd.z, _cmd.f)
        elif cmd.lower().startswith('g0'): # G0 команда (без ограничений по rect)
            _cmd = self.parse_g0(cmd)
            return self.send_read(f'G0 X{_cmd.x} Y{_cmd.y} Z{_cmd.z} F{_cmd.f}')
        elif cmd.lower().startswith('m114'): # Опрос текущих координат и вывод
            self.m114()
            return self.pos()
        elif cmd == 'probe': # одиночная проба
            self.probing()
            return self.pos()
        elif cmd == 'probing rect' or cmd == 'probing_rect': # проба по rect с записью отклонений
            self.probe_from_rectangle()
            self.m114()
            return self.pos()
        elif cmd == 'map':
            self.draw_deviation_map_table()
            return None
        elif cmd == 'save map' or cmd == 'save_map':
            self.save_map_to_file()
        elif cmd.startswith('modify_file '):
            cmd = cmd.replace('modify_file ', '')
            self.modify_file(cmd)
            return 'done!'
        else: # отправка с ответом всех остальных команд
            return f'answer: {self.send_read(cmd)}'
