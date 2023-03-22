import os
import typing as t
from dataclasses import dataclass

from deploy.Windows.utils import cached_property, iter_folder


def abspath(path):
    return os.path.abspath(path).replace('\\', '/')


def get_serial_pair(serial):
    """
    Args:
        serial (str):

    Returns:
        str, str: `127.0.0.1:5555+{X}` and `emulator-5554+{X}`, 0 <= X <= 32
    """
    if serial.startswith('127.0.0.1:'):
        try:
            port = int(serial[10:])
            if 5555 <= port <= 5555 + 32:
                return f'127.0.0.1:{port}', f'emulator-{port - 1}'
        except (ValueError, IndexError):
            pass
    if serial.startswith('emulator-'):
        try:
            port = int(serial[9:])
            if 5554 <= port <= 5554 + 32:
                return f'127.0.0.1:{port + 1}', f'emulator-{port}'
        except (ValueError, IndexError):
            pass

    return None, None


@dataclass
class EmulatorInstanceBase:
    # Serial for adb connection
    serial: str
    # Emulator instance name, used for start/stop emulator
    name: str
    # Path to emulator .exe
    path: str

    def __str__(self):
        return f'{self.type}(serial="{self.serial}", name="{self.name}", path="{self.path}")'

    @cached_property
    def type(self) -> str:
        """
        Returns:
            str: Emulator type, such as Emulator.NoxPlayer
        """
        return EmulatorBase.path_to_type(self.path)

    @cached_property
    def emulator(self):
        """
        Returns:
            Emulator:
        """
        return EmulatorBase(self.path)

    def __eq__(self, other):
        if isinstance(other, str) and self.type == other:
            return True
        if isinstance(other, list) and self.type in other:
            return True
        if isinstance(other, EmulatorInstanceBase):
            return super().__eq__(other) and self.type == other.type
        return super().__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def __bool__(self):
        return True


class EmulatorBase:
    NoxPlayer = 'NoxPlayer'
    NoxPlayer64 = 'NoxPlayer64'
    NoxPlayerFamily = [NoxPlayer, NoxPlayer64]
    BlueStacks4 = 'BlueStacks4'
    BlueStacks5 = 'BlueStacks5'
    BlueStacks4HyperV = 'BlueStacks4HyperV'
    BlueStacks5HyperV = 'BlueStacks5HyperV'
    BlueStacksFamily = [BlueStacks4, BlueStacks5]
    LDPlayer3 = 'LDPlayer3'
    LDPlayer4 = 'LDPlayer4'
    LDPlayer9 = 'LDPlayer9'
    LDPlayerFamily = [LDPlayer3, LDPlayer4, LDPlayer9]
    MumuPlayer = 'MumuPlayer'
    MumuPlayer9 = 'MumuPlayer9'
    MumuPlayer12 = 'MumuPlayer12'
    MumuPlayerFamily = [MumuPlayer, MumuPlayer9, MumuPlayer12]
    MemuPlayer = 'MemuPlayer'

    @classmethod
    def path_to_type(cls, path: str) -> str:
        """
        Args:
            path: Path to .exe file

        Returns:
            str: Emulator type, such as Emulator.NoxPlayer,
                or '' if this is not a emulator.
        """
        return ''

    def iter_instances(self) -> t.Iterable[EmulatorInstanceBase]:
        """
        Yields:
            EmulatorInstance: Emulator instances found in this emulator
        """
        pass

    def iter_adb_binaries(self) -> t.Iterable[str]:
        """
        Yields:
            str: Filepath to adb binaries found in this emulator
        """
        pass

    def __init__(self, path):
        # Path to .exe file
        self.path = path.replace('\\', '/')
        # Path to emulator folder
        self.dir = os.path.dirname(path)
        # str: Emulator type, or '' if this is not a emulator.
        self.type = self.__class__.path_to_type(path)

    def __eq__(self, other):
        if isinstance(other, str) and self.type == other:
            return True
        if isinstance(other, list) and self.type in other:
            return True
        return super().__eq__(other)

    def __str__(self):
        return f'{self.type}(path="{self.path}")'

    __repr__ = __str__

    def __hash__(self):
        return hash(self.path)

    def __bool__(self):
        return True

    def abspath(self, path, folder=None):
        if folder is None:
            folder = self.dir
        return abspath(os.path.join(folder, path))

    @classmethod
    def is_emulator(cls, path: str) -> bool:
        """
        Args:
            path: Path to .exe file.

        Returns:
            bool: If this is a emulator.
        """
        return bool(cls.path_to_type(path))

    def list_folder(self, folder, is_dir=False, ext=None):
        """
        Safely list files in a folder

        Args:
            folder:
            is_dir:
            ext:

        Returns:
            list[str]:
        """
        folder = self.abspath(folder)
        try:
            return list(iter_folder(folder, is_dir=is_dir, ext=ext))
        except FileNotFoundError:
            return []


class EmulatorManagerBase:
    @cached_property
    def all_emulators(self) -> t.List[EmulatorBase]:
        """
        Get all emulators installed on current computer.
        """
        return []

    @cached_property
    def all_emulator_instances(self) -> t.List[EmulatorInstanceBase]:
        """
        Get all emulator instances installed on current computer.
        """
        return []

    @cached_property
    def all_emulator_serials(self) -> t.List[str]:
        """
        Returns:
            list[str]: All possible serials on current computer.
        """
        out = []
        for emulator in self.all_emulator_instances:
            out.append(emulator.serial)
            # Also add serial like `emulator-5554`
            port_serial, emu_serial = get_serial_pair(emulator.serial)
            if emu_serial:
                out.append(emu_serial)
        return out

    @cached_property
    def all_adb_binaries(self) -> t.List[str]:
        """
        Returns:
            list[str]: All adb binaries of emulators on current computer.
        """
        out = []
        for emulator in self.all_emulators:
            for exe in emulator.iter_adb_binaries():
                out.append(exe)
        return out
