""""""

import science_mode_4 as sm4


class ScienceModeDevice:
    """Thin wrapper around a ScienceMode4 device"""

    def __init__(self, com_port: str | None):
        self._measurement_active = False
        self._com_port = com_port

        # create serial port connection
        self._connection: sm4.SerialPortConnection = None
        # if no com port was passed, auto detect a ScienceMode device
        if self._com_port is None:
            port = sm4.SerialPortConnection.list_science_mode_device_ports()[0]
            self._connection = sm4.SerialPortConnection(port.device)
        else:
            self._connection = sm4.SerialPortConnection(self._com_port)


    async def connect(self) -> None:
        """Connect device"""
        # open connection, now we can read and write data
        self._connection.open()


    async def disconnect(self) -> None:
        """Disconnect device"""
        self._connection.close()


    async def handle_command(self, command: str) -> bool:
        """Handles a command, returns True if programm should terminate"""
        if command == "START":
            await self._start()
            return False
        if command == "STOP":
            await self._stop()
            return True


    async def get_measurement_data(self) -> list[float] | None:
        """Get measurement data"""
        return None


    def get_available_commands(self) -> list[str]:
        """Returns all available commands"""
        return ["START", "STOP"]


    async def _start(self) -> None:
        """Start measurement"""
        self._measurement_active = True


    async def _stop(self) -> None:
        """Stop measurement"""
        self._measurement_active = False
