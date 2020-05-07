"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport
    decodedlogin: str



    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)
        self.server.history.append(decoded)
        decodedlogin = None

        if decoded.startswith("login:"):
            decodedlogin = decoded[6:len(decoded)]

        if decodedlogin in self.server.logins:
            self.transport.write(
                f"Логин {decodedlogin} занят!".encode()
            )
            self.transport.close()

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                self.transport.write(
                    f"Привет, {self.login}!".encode()
                )
                self.server.logins.append(self.login)
                self.send_history()
        else:
            self.send_message(decoded)


    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        historym = ("история сообщений: ")
        history = ' '.join(self.server.history)
        for client in self.server.clients:
            if client.login == self.login:

                client.transport.write(historym.encode())
                client.transport.write(history.encode())



    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    logins: list
    history: list

    def __init__(self):
        self.clients = []
        self.logins = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
