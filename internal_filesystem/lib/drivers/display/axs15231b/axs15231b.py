from micropython import const
import display_driver_framework
import lcd_bus
import lvgl as lv


STATE_HIGH = display_driver_framework.STATE_HIGH
STATE_LOW = display_driver_framework.STATE_LOW
STATE_PWM = display_driver_framework.STATE_PWM

BYTE_ORDER_RGB = display_driver_framework.BYTE_ORDER_RGB
BYTE_ORDER_BGR = display_driver_framework.BYTE_ORDER_BGR

_RASET = const(0x2B)
_CASET = const(0x2A)
_MADCTL = const(0x36)

_RAMWR = const(0x2C)
_RAMWRC = const(0x3C)

_WRITE_CMD = const(0x02)
_WRITE_COLOR = const(0x32)

_MADCTL_MV = const(0x20)
_MADCTL_MX = const(0x40)
_MADCTL_MY = const(0x80)


class AXS15231B(display_driver_framework.DisplayDriver):
    _ORIENTATION_TABLE = (
        0x0,
        _MADCTL_MV | _MADCTL_MX,
        _MADCTL_MY | _MADCTL_MX,
        _MADCTL_MV | _MADCTL_MY
    )

    def __init__(
        self,
        data_bus,
        display_width,
        display_height,
        frame_buffer1=None,
        frame_buffer2=None,
        reset_pin=None,
        reset_state=STATE_HIGH,
        power_pin=None,
        power_on_state=STATE_HIGH,
        backlight_pin=None,
        backlight_on_state=STATE_HIGH,
        offset_x=0,
        offset_y=0,
        color_byte_order=BYTE_ORDER_RGB,
        color_space=lv.COLOR_FORMAT.RGB565,
        rgb565_byte_swap=False,
    ):
        num_lanes = data_bus.get_lane_count()

        if isinstance(data_bus, lcd_bus.SPIBus) and num_lanes == 4:
            self._qspi = True
            _cmd_bits = 32
        else:
            self._qspi = False
            _cmd_bits = 8

        if color_space != lv.COLOR_FORMAT.RGB565:
            rgb565_byte_swap = False

        self._rgb565_byte_swap = rgb565_byte_swap

        super().__init__(
            data_bus=data_bus,
            display_width=display_width,
            display_height=display_height,
            frame_buffer1=frame_buffer1,
            frame_buffer2=frame_buffer2,
            reset_pin=reset_pin,
            reset_state=reset_state,
            power_pin=power_pin,
            power_on_state=power_on_state,
            backlight_pin=backlight_pin,
            backlight_on_state=backlight_on_state,
            offset_x=offset_x,
            offset_y=offset_y,
            color_byte_order=color_byte_order,
            color_space=color_space,
            rgb565_byte_swap=rgb565_byte_swap,
            _cmd_bits=_cmd_bits,
            _param_bits=8,
            _init_bus=True
        )

    def set_params(self, cmd, params=None):
        if self._qspi:
            cmd &= 0xFF
            cmd <<= 8
            cmd |= _WRITE_CMD << 24
        self._data_bus.tx_param(cmd, params)

    def _set_memory_location(self, x1, y1, x2, y2):
        if y1 == 0:
            cmd = _RAMWR
        else:
            cmd = _RAMWRC

        param_buf = self._param_buf

        param_buf[0] = (x1 >> 8) & 0xFF
        param_buf[1] = x1 & 0xFF
        param_buf[2] = (x2 >> 8) & 0xFF
        param_buf[3] = x2 & 0xFF

        self._data_bus.tx_param(_CASET, self._param_mv)

        if self._qspi:
            cmd &= 0xFF
            cmd <<= 8
            cmd |= _WRITE_COLOR << 24
        else:
            param_buf[0] = (y1 >> 8) & 0xFF
            param_buf[1] = y1 & 0xFF
            param_buf[2] = (y2 >> 8) & 0xFF
            param_buf[3] = y2 & 0xFF
            self._data_bus.tx_param(_RASET, self._param_mv)

        return cmd
