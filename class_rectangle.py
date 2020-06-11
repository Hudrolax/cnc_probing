class Point:
    def __init__(self, x, y, dev:float=0):
        if isinstance(x, float) or isinstance(x, int):
            self._x = x
        else:
            raise TypeError(f'Point x setter type error {type(x)}. Need float or int.')
        if isinstance(y, float) or isinstance(y, int):
            self._y = y
        else:
            raise TypeError(f'Point y setter type error {type(y)}. Need float or int.')
        if isinstance(dev, float) or isinstance(dev, int):
            self._deviation = dev
        else:
            raise TypeError(f'Point deviation setter type error {type(dev)}. Need float or int.')

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        if isinstance(val, float) or isinstance(val, int):
            self._y = val
        else:
            raise TypeError(f'Point y setter type error {type(val)}. Need float or int.')

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        if isinstance(val, float) or isinstance(val, int):
            self._x = val
        else:
            raise TypeError(f'Point x setter type error {type(val)}. Need float or int.')

    @property
    def deviation(self):
        return self._deviation

    @deviation.setter
    def deviation(self, val):
        if isinstance(val, float) or isinstance(val, int):
            self._deviation = val
        else:
            raise TypeError(f'Point deviation setter type error {type(val)}. Need float or int.')

    def __str__(self):
        return f'X{self.x} Y{self.y} dev {self.deviation}'

    def __eq__(self, other):
        if isinstance(other, Point):
            if self.x == other.x and self.y == other.y:
                return True
            else:
                return False
        else:
            raise Exception(f'Wrong type of eq {type(other)}')

    def __ne__(self, other):
        if isinstance(other, Point):
            if self.x != other.x or self.y != other.y:
                return True
            else:
                return False
        else:
            raise Exception(f'Wrong type of eq {type(other)}')

class Rectangle:
    def __init__(self, x_max, y_max):
        self.x_max = x_max
        self.y_max = y_max
        self.probe_ident = 0
        self.probe_net = (7, 7)
        self.x_probe_points = []
        self.y_probe_points = []
        self.points = []
        self.x_step = round((self.x_max - self.probe_ident * 2) / (self.probe_net[0] - 1), 4)
        self.y_step = round((self.y_max - self.probe_ident * 2) / (self.probe_net[1] - 1), 4)

        # print(f"X step: {self.x_step}")
        # print(f"Y step: {self.y_step}")
        x_point = self.probe_ident
        y_point = self.probe_ident
        for x in range(0, self.probe_net[0]):
            # print(f'x point {x_point}')
            self.x_probe_points.append(x_point)
            x_point = round(x_point + self.x_step, 4)

        for y in range(0, self.probe_net[1]):
            # print(f'y point {y_point}')
            self.y_probe_points.append(y_point)
            y_point = round(y_point + self.y_step, 4)

        for x in self.x_probe_points:
            for y in self.y_probe_points:
                _point = Point(x,y)
                self.points.append(_point)
                # print(_point)

    def get_point(self, _point):
        for point in self.points:
            if point.x == _point.x and point.y == _point.y:
                return point

    def get_nearest_value(self, _point):
        x_points = []
        y_points = []
        for point in self.points:
            if point.x <= _point.x and point.y <= _point.y:
                x_points.append(point.x)
                y_points.append(point.y)

        x_points.sort()
        y_points.sort()
        for point in self.points:
            if point.x == x_points[-1] and point.y == y_points[-1]:
                return point

    @staticmethod
    def map(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def __getitem__(self, item):
        # print(f'rect: item = {item} type({type(item)})')
        # 3---4
        # -----   point map
        # 1---2
        if isinstance(item, tuple):
            # сначала поищем точку среди тех, где были замеры отклонений
            _point = self.get_point(Point(item[0], item[1]))
            if _point is not None:
                return _point

            # Найдем ближайшие точки
            nearest_point = self.get_nearest_value(Point(item[0], item[1]))
            # print(f'nearest_point {nearest_point}')

            point_1 = self.get_point(nearest_point)
            p2_x = nearest_point.x+self.x_step
            if p2_x > self.x_max:
                p2_x = nearest_point.x
            point_2 = self.get_point(Point(p2_x, nearest_point.y))
            p3_y = nearest_point.y + self.y_step
            if p3_y > self.y_max:
                p3_y = nearest_point.y
            point_3 = self.get_point(Point(nearest_point.x,p3_y))
            p4_x = nearest_point.x + self.x_step
            if p4_x > self.x_max:
                p4_x = nearest_point.x
            p4_y = nearest_point.y + self.y_step
            if p4_y > self.y_max:
                p4_y = nearest_point.y
            point_4 = self.get_point(Point(p4_x, p4_y))

            if point_1 is not None and point_2 is not None and point_3 is not None and point_4 is not None:
                point_12 = Point(item[0], nearest_point.y, self.map(item[0], nearest_point.x, nearest_point.x + self.x_step, point_1.deviation, point_2.deviation))
                point_34 = Point(item[0], nearest_point.y, self.map(item[0], nearest_point.x, nearest_point.x + self.x_step, point_3.deviation, point_4.deviation))
                point_our = Point(item[0], item[1], round(self.map(item[1], nearest_point.y, nearest_point.y + self.y_step, point_12.deviation, point_34.deviation),4))
                # print(f'p1 {point_1}')
                # print(f'p2 {point_2}')
                # print(f'p3 {point_3}')
                # print(f'p4 {point_4}')
                # print(f'our {point_our}')
            else:
                raise Exception('rect error')
                # point_our = Point(item[0], item[1])

            # print(f'3({point_3.x},{point_3.y})[{point_3.deviation}]--34({point_34.x},{point_34.y})[{point_34.deviation}]--4({point_4.x},{point_4.y})[{point_4.deviation}]')
            # print(f'-----------our({point_our.x},{point_our.y})[{point_our.deviation}]-----------')
            # print(f'1({point_1.x},{point_1.y})[{point_1.deviation}]--12({point_12.x},{point_12.y})[{point_12.deviation}]--2({point_2.x},{point_2.y})[{point_2.deviation}]')
            return point_our
        else:
            raise TypeError(f'Rectangle wrong type {type(item)}. Need typle.')


if __name__ == '__main__':
    rect = Rectangle(15, 15)
