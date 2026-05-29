from pydantic import BaseModel, SecretStr


class Ssh:

    def __init__(self, config: SftpConfig) -> None:
        self.host = config.host
        self.port = config.port
        self.username = config.username
        self.password = config.password.get_secret_value()
        self.key_filename = config.key_filename
        self.known_hosts = config.known_hosts
        self.out_path = "/IN/"
        self.connected = False

    def connect(self):
        from paramiko import SSHClient, SFTPClient, RejectPolicy

        self.ssh: SSHClient = SSHClient()
        if self.known_hosts:
            self.ssh.load_host_keys(self.known_hosts)
        self.ssh.load_system_host_keys()
        # self.ssh.set_missing_host_key_policy(RejectPolicy())
        self.ssh.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=30,
        )
        self.sftp: SFTPClient = self.ssh.open_sftp()
        self.connected = True

    def ensure_remote_dir(self, remote_dir):
        if not self.connected:
            self.connect()
        parts = remote_dir.strip("/").split("/")
        current = ""
        for part in parts:
            current = f"{current}/{part}"
            return self.sftp.stat(current)

    def list_dir(self, remote_dir):
        if not self.connected:
            self.connect()
        parts = remote_dir.strip("/").split("/")
        current = ""
        for part in parts:
            current = f"{current}/{part}"
            return self.sftp.listdir(current)


class SshConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 22
    username: str = "UserToChange"
    password: SecretStr = SecretStr("ChangeMeNow")
    key_filename: str = ""
    known_hosts: str = ""
