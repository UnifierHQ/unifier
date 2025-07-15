class WebhookCacheStore:
    def __init__(self, bot):
        self.__bot = bot
        self.__webhooks = {}

    def store_webhook(self, webhook, identifier, server):
        self.__webhooks.setdefault(server, {})[identifier] = webhook
        return len(self.__webhooks[server])

    def store_webhooks(self, webhooks: list, identifiers: list, servers: list):
        if not len(webhooks) == len(identifiers) == len(servers):
            raise ValueError('webhooks, identifiers, and servers must be the same length')

        for index in range(len(webhooks)):
            webhook = webhooks[index]
            identifier = identifiers[index]
            server = servers[index]
            self.__webhooks.setdefault(server, {})[identifier] = webhook
        return len(self.__webhooks)

    def get_webhooks(self, server: int or str):
        try:
            server = int(server)
        except:
            pass

        if len(self.__webhooks[server].values())==0:
            raise ValueError('no webhooks')
        return list(self.__webhooks[server].values())

    def get_webhook(self, identifier: int or str):
        try:
            identifier = int(identifier)
        except:
            pass

        for guild in self.__webhooks.keys():
            if identifier in self.__webhooks[guild].keys():
                return self.__webhooks[guild][identifier]
        raise ValueError('invalid webhook')

    def clear(self, server: int or str = None):
        if not server:
            self.__webhooks = {}
        else:
            self.__webhooks[server] = {}
        return
