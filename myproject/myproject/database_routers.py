class WebsocketDatabaseRouter:
    websocket_database = "websocket"
    websocket_model = "chatmessage"

    def _is_websocket_model(self, model):
        return model._meta.model_name == self.websocket_model

    def db_for_read(self, model, **hints):
        if self._is_websocket_model(model):
            return self.websocket_database
        return None

    def db_for_write(self, model, **hints):
        if self._is_websocket_model(model):
            return self.websocket_database
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if self._is_websocket_model(obj1) or self._is_websocket_model(obj2):
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == self.websocket_model:
            return db == self.websocket_database
        if db == self.websocket_database:
            return False
        return None