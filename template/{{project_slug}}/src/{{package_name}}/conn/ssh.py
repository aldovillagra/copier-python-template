from pathlib import Path
from typing import Optional

from pydantic import BaseModel, SecretStr


class SSHConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 22
    username: str = "UserToChange"
    password: Optional[SecretStr] = SecretStr("ChangeMeNow")
    key_filename: Optional[str] = None
    known_hosts: Optional[str] = None
    allow_unknown_hosts: bool = False


class SSH:
    def __init__(self, config: SSHConfig) -> None:
        from paramiko import SSHClient
        self.config = config
        self.ssh: Optional[SSHClient] = None
        self.connected = False

    def connect(self):
        from paramiko import SSHClient, AutoAddPolicy
        if self.connected and self.ssh:
            return self.ssh

        self.ssh = SSHClient()

        if self.config.known_hosts:
            self.ssh.load_host_keys(self.config.known_hosts)

        self.ssh.load_system_host_keys()

        if self.config.allow_unknown_hosts:
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())

        self.ssh.connect(
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=(
                self.config.password.get_secret_value()
                if self.config.password
                else None
            ),
            key_filename=self.config.key_filename or None,
            timeout=30,
        )

        self.connected = True

    def disconnect(self) -> None:
        if self.ssh:
            self.ssh.close()

        self.connected = False
        self.ssh = None


class SFTP(SSH):
    def __init__(self, config: SSHConfig) -> None:
        super().__init__(config)
        from paramiko import SFTPClient, SSHClient
        self.sftp: SFTPClient = SFTPClient()

    def connect(self):
        super().connect()
        self.sftp = self.ssh.open_sftp()

    def disconnect(self) -> None:
        if self.sftp:
            self.sftp.close()

        super().disconnect()

    def list_dir(self, remote_dir: str) -> list[str]:
        sftp = self.connect()
        return self.sftp.listdir(remote_dir)

    def put_file(self, local_output: str | Path, remote_output: str) -> None:
        self.sftp.put(str(local_output), remote_output)

    def get_file(self, remote_input: str, local_input: str | Path) -> None:
        self.sftp.get(remote_input, str(local_input))

    def move_file(self, old_path: str, new_path: str) -> None:
        self.sftp.rename(old_path, new_path)

    def remove_file(self, current_path: str) -> None:
        self.sftp.remove(current_path)

    def ensure_remote_dir(self, remote_dir: str) -> None:
        current = ""
        for part in remote_dir.strip("/").split("/"):
            current = f"{current}/{part}"
            try:
                self.sftp.stat(current)
            except FileNotFoundError:
                self.sftp.mkdir(current)
