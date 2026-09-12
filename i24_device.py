""""""

import science_mode_4 as sm4

from sm4_device import ScienceModeDevice



class I24Device(ScienceModeDevice):
    """Thin wrapper around a I24 device"""

    def __init__(self, com_port: str | None):
        super().__init__(com_port)
        self._device = sm4.DeviceI24(self._connection)
        self._layer = self._device.get_layer_dyscom()


    async def get_measurement_data(self) -> list[float] | None:
        ack = self._layer.packet_buffer.get_packet_from_buffer()
        if ack:
            if ack.command == sm4.Commands.DL_SEND_LIVE_DATA:
                sld: sm4.PacketDyscomSendLiveData = ack
                return [sld.samples[0].value]

        return None


    async def _start(self) -> None:
        await super()._start()

        # call enable measurement power module for measurement
        await self._layer.power_module(sm4.DyscomPowerModuleType.MEASUREMENT, 
                                       sm4.DyscomPowerModulePowerType.SWITCH_ON)
        # call init with lowest sample rate and enable signal types
        init_params = sm4.DyscomInitParams()
        init_params.signal_type = [sm4.DyscomSignalType.EMG_1]
        init_params.register_map_ads129x.config_register_1.output_data_rate = sm4.Ads129xOutputDataRate.HR_MODE_500_SPS__LP_MODE_250_SPS
        init_params.register_map_ads129x.config_register_1.power_mode = sm4.Ads129xPowerMode.LOW_POWER
        await self._layer.init(init_params)

        # start dyscom measurement
        await self._layer.start()


    async def _stop(self) -> None:
        await self._layer.stop()
        await super()._stop()
