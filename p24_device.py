""""""

import science_mode_4 as sm4

from sm4_device import ScienceModeDevice



class P24Device(ScienceModeDevice):
    """Thin wrapper around a P24 device"""

    def __init__(self, com_port: str | None):
        super().__init__(com_port)
        self._device = sm4.DeviceP24(self._connection)
        self._layer = self._device.get_layer_low_level()

        self._stim_pattern_1 = [sm4.ChannelPoint(500, 30),
            sm4.ChannelPoint(500, 0), sm4.ChannelPoint(500, -30),
            sm4.ChannelPoint(500, 0)]
        self._stim_pattern_2 = [sm4.ChannelPoint(200, 15),
            sm4.ChannelPoint(200, 30), sm4.ChannelPoint(200, 45),
            sm4.ChannelPoint(200, 60), sm4.ChannelPoint(200, 0),
            sm4.ChannelPoint(200, -60),
            sm4.ChannelPoint(200, -45), sm4.ChannelPoint(200, -30),
            sm4.ChannelPoint(200, -15), sm4.ChannelPoint(200, 0)]


    async def handle_command(self, command: str) -> bool:
        if self._measurement_active:
            if command == "STIM_1":
                self._layer.send_channel_config(True, sm4.Channel.RED, sm4.Connector.YELLOW,
                                                self._stim_pattern_1)
                return False
            if command == "STIM_2":
                self._layer.send_channel_config(True, sm4.Channel.RED, sm4.Connector.GREEN,
                                                self._stim_pattern_2)
                return False

        return await super().handle_command(command)



    async def get_measurement_data(self) -> list[float] | None:
        ack = self._layer.packet_buffer.get_packet_from_buffer()
        if ack:
            if ack.command == sm4.Commands.LOW_LEVEL_CHANNEL_CONFIG_ACK:
                ll_config_ack: sm4.PacketLowLevelChannelConfigAck = ack
                return ll_config_ack.measurement_samples

        return None


    def get_available_commands(self) -> list[str]:
        return super().get_available_commands() + ["STIM_1", "STIM_2"]


    async def _start(self) -> None:
        await super()._start()

        await self._device.initialize()
        try:
            # sometime activating high voltage may cause a communication interrupt
            await self._layer.init(sm4.LowLevelMode.STIM_CURRENT,
                                   sm4.LowLevelHighVoltageSource.STANDARD)
        except Exception as e:
            print(e)


    async def _stop(self) -> None:
        await self._layer.stop()
        await super()._stop()
