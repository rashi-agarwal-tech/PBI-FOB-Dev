from airflow.hooks.base import BaseHook


class PowerBiHook(BaseHook):
    default_conn_name = "powerbi"

    def __init__(self, power_bi_conn_id=default_conn_name):
        super().__init__()
        self.conn = self.get_connection(power_bi_conn_id)
        self._client_id = self.conn.extra_dejson["client_id"]
        self._client_secret = self.conn.extra_dejson["client_secret"]
