import enum


class NVMEAdminCommands(enum.IntEnum):
    IDENTIFY = 0x06


IOCTL_NVME_ADMIN_CMD = 0xC0484E41
