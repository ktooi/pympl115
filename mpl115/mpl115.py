# -*- coding: utf-8 -*-
import time
import smbus
from logging import getLogger


logger = getLogger(__name__)
usleep = lambda x: time.sleep(x/1000000.0)  # noqa


class MPL115(object):
    """ MPL115 に対応する Python モジュールです。

    センサーから気温及び湿度を取得します。また、取得した気温及び湿度から不快指数を計算することもできます。

    Examples:

        次のようにシンプルに使うことができます。

        Simple usage is as follows.

        >>> from mpl115 import MPL115
        >>>
        >>> mpl115 = MPL115(name="mpl115")
        >>>
        >>> mpl115.humidity
        >>> mpl115.temperature
        >>> mpl115.discomfort

        次のように、センサーとの通信のタイミングを細かく制御することもできます。

        The timing of communication with the sensor can also be finely controlled, as shown below.

        >>> from mpl115 import MPL115
        >>>
        >>> mpl115 = MPL115(name="mpl115", wakeup=False)
        >>>
        >>> mpl115.wakeup()
        >>> mpl115.set_write_mode()
        >>> mpl115.measure()
        >>> mpl115.read()
        >>>
        >>> mpl115.humidity
        >>> mpl115.temperature
        >>> mpl115.discomfort
    """

    # MPL115 の I2C アドレス。
    # I2C address of MPL115.
    chip_addr = 0x60

    # define wait micro sec.
    wait_conversion = 3000

    def __init__(self, name="mpl115", bus=1, wakeup=True, retry_wait=20000, retry_num=10):
        self._name = name
        self._i2c = smbus.SMBus(bus)
        self._bus = bus
        self._retry_wait = retry_wait
        self._retry_num = retry_num
        self._start_conversion = False

    @classmethod
    def convert_coefficient(cls, msb, lsb, total_bits, fractional_bits, zero_pad):
        result = float((((msb & 0x7F) << 8) + lsb ) / float(1 << 16 - total_bits + fractional_bits + zero_pad ))
        if (msb >> 7) == 1:
            result = -result;
        return result

    def start_conversion(self):
        """ MPL115 を書き込みモードにするメソッドです。"""
        i2c = self._i2c
        # 0x12 ... Start Pressure and Temperature Conversion
        # 0x01 ... 10-bit Pressure ADC output value LSB(2bit)
        i2c.write_byte_data(address, 0x12, 0x01)
        self._start_conversion = True
        usleep(self.wait_conversion)

    def read_data(self):
        i2c = self._i2c
        if not self._start_conversion:
            self.start_conversion()
        self._data = i2c.read_i2c_block_data(address, 0x00, 12) 

    @property
    def a0(self):
        data = self._data
        if not hasattr(self, "_a0"):
            self._a0 = MPL115.convert_coefficient(data[4], data[5], 16, 3, 0)
        return self._a0

    @property
    def b1(self):
        data = self._data
        if not hasattr(self, "_b1"):
            self._b1 = MPL115.convert_coefficient(data[6], data[7], 16, 13, 0)
        return self._b1

    @property
    def b2(self):
        data = self._data
        if not hasattr(self, "_b2"):
            self._b2 = MPL115.convert_coefficient(data[8], data[9], 16, 14, 0)
        return self._b2

    @property
    def c12(self):
        data = self._data
        if not hasattr(self, "_c12"):
            self._c12 = MPL115.convert_coefficient(data[10], data[11], 14, 13, 9)
        return self._c12

    @property
    def padc(self):
        data = self._data
        if not hasattr(self, "_padc"):
            self._padc = (data[0] << 8 | data[1]) >> 6
        return self._padc

    @property
    def tadc(self):
        data = self._data
        if not hasattr(self, "_tadc"):
            self._tadc = (data[2] << 8 | data[3]) >> 6
        return self._tadc

    @property
    def c12x2(self):
        if not hasattr(self, "_c12x2"):
            self._c12x2 = self.c12() * self.tadc()
        return self._c12x2

    @property
    def a1(self):
        if not hasattr(self, "_a1"):
            self._a1 = self.b1() + self.c12x2()
        return self._a1

    @property
    def a1x1(self):
        if not hasattr(self, "_a1x1"):
            self._a1x1= self.a1() * self.padc()
        return self._a1x1

    @property
    def y1(self):
        if not hasattr(self, "_y1"):
            self._y1 = self.a0() * self.a1x1()
        return self._y1

    @property
    def a2x2(self):
        if not hasattr(self, "_a2x2"):
            self._a2x2 = self.b2() * self.tadc()
        return self._a2x2

    @property
    def pcomp(self):
        if not hasattr(self, "_pcomp"):
            self._pcomp = self.y1() + self.a2x2()
        return self._pcomp

    @property
    def pressure(self):
        if not hasattr(self, "_pressure"):
            self._pressure = (self.pcomp() * 65 / 1023) + 50
        return self._pressure

    @property
    def hectopascal(self):
        if not hasattr(self, "_hectopascal"):
            self._hectopascal = self.pressure() * 10
        return self._hectopascal
