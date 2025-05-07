import json
import uuid
import datetime
from py3xui import AsyncApi, Client

class XUIClient:
    def __init__(self, config_file="../settings/servers.json"):
        """
        Download servers' config from JSON
        :param config_file: Name file with servers data
        """
        with open(config_file, "r") as f:
            self.servers = json.load(f)
            f.close()

        """
        Initial Api for all servers
        """
        for server_name, server_data in self.servers.items():
            self.servers[server_name]["api"] = AsyncApi(
                host=server_data["host"],
                username=server_data["username"],
                password=server_data["password"]
            )

    async def login_all(self):
        for _, server_data in self.servers.items():
            await server_data["api"].login()


    async def create_client(self, user_id: int, duration: datetime.timedelta, server: str, protocol : str = None) -> str:
        """
        Create a new client for inbound
        :param user_id: User id form telegram
        :param duration: 1 d/w/m ...
        :param server: france/germany...
        :param protocol: Vless / SS
        :return: String for connection
        """
        if server not in self.servers:
            raise ValueError(f"Сервер {server} не поддерживается.")

        server_data = self.servers[server]
        email = f"user_{user_id}"
        expiry_time = int((datetime.datetime.now() + duration).timestamp() * 1000)

        client = Client(
            id=str(uuid.uuid4()),
            email=email,
            enable=True,
            flow="xtls-rprx-vision",
            expiry_time=expiry_time,
            tg_id=user_id,
            inbound_id=1,  # It's assumed that the inbound_id is the same for all servers
        )

        await server_data["api"].client.add(1, [client])
        return await self.get_connection_string(client.id, email, server, protocol)

    async def get_connection_string(self, user_uuid: str, user_email: str, server: str, protocol : str = None) -> str:
        """
        :param user_uuid: uuid4()
        :param user_email: email_{id telegram}
        :param server: france/germany...
        :param protocol: Vless / SS
        :return: String for connection
        """
        if server not in self.servers:
            raise ValueError(f"Сервер {server} не поддерживается.")

        server_data = self.servers[server]
        inbound = await server_data["api"].inbound.get_by_id(1)
        settings = inbound.stream_settings.reality_settings

        return (
            f"vless://{user_uuid}@{server_data['external_ip']}:{server_data['port']}"
            f"?type=tcp&security=reality&pbk={settings['settings']['publicKey']}&fp=chrome"
            f"&sni={settings['serverNames'][0]}&sid={settings['shortIds'][0]}"
            f"&spx=%2F&flow=xtls-rprx-vision#{server_data['remark']}-{user_email}"
        )

    async def get_subscription_status(self, user_id: int) -> dict:
        """
        Returns all subscription status
        :param user_id:
        :return:
        """
        status = {}
        for server_name, _ in self.servers.items():
            clients = await self.get_list_of_users(server_name)
            for client in clients:
                if str(client.tg_id) == str(user_id):
                    expiry = datetime.datetime.fromtimestamp(client.expiry_time / 1000)
                    status[server_name] = {
                        "active": expiry > datetime.datetime.now(),
                        "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"),
                        "email": client.email,
                        "id": client.id
                    }
        return status if status else None

    async def renew_subscription(self, user_id: int, duration: datetime.timedelta, server: str, protocol : str = None) -> None:
        """
        Renew subscription
        :param user_id: id-tg
        :param duration: 1 d/w/m...
        :param server: fr/ger/...
        :param protocol: Vless/SS
        :return:
        """
        if server not in self.servers:
            raise ValueError(f"Сервер {server} не поддерживается.")

        clients = await self.get_list_of_users(server)

        for client in clients:
            if str(client.tg_id) == str(user_id):
                current_expiry = datetime.datetime.fromtimestamp(client.expiry_time / 1000)
                # If the subscription is still active, we will extend it from the current end date.
                new_expiry = max(current_expiry, datetime.datetime.now()) + duration
                client.expiry_time = int(new_expiry.timestamp() * 1000)
                await self.servers[server]["api"].client.update(client.id, client)
                return


    async def get_list_of_users(self, server : str) -> list:
        server_data = self.servers[server]
        inbound = await server_data["api"].inbound.get_by_id(1)
        return inbound.settings.clients