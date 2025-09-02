import http

import requests
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException
from settings import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=30),
    stop=stop_after_delay(120),
    retry=retry_if_exception_type(ServerException),
)
def ping():
    try:
        response = requests.get("http://" + settings.clickhouse.host + ":8123")
        if (
            response.status_code != http.HTTPStatus.OK
            or response.text != "Ok.\n"
        ):
            return False
        return True
    except:
        return False


class ClickhouseWriter:
    def __init__(
        self,
    ):
        self.client = Client(host=settings.clickhouse.host)
        self.settings_by_table = {}
        for model_tuple in settings.topics:
            model = model_tuple[1]
            self.settings_by_table[model["table"]] = model

    def start_up(self):
        self.client.execute(
            "CREATE DATABASE IF NOT EXISTS analytic"
            " ON CLUSTER company_cluster",
        )
        for model_tuple in settings.topics:
            model = model_tuple[1]
            model_fields = [
                field + " " + field_type
                for (field, field_type) in model["fields"].items()
            ]
            self.client.execute(
                "CREATE TABLE IF NOT EXISTS analytic."
                + model["table"]
                + " ON CLUSTER company_cluster "
                "(id UUID," + ", ".join(model_fields) + ",PRIMARY KEY (id)) "
                "Engine=MergeTree() ORDER BY id",
            )

    def write(self, msgs_list):
        msgs_by_table = {}
        for model_tuple in settings.topics:
            model = model_tuple[1]
            msgs_by_table[model["table"]] = []
        for msg in msgs_list:
            msg_table = msg["table"]
            msg_fields = []
            if msg_table and msg["table"] in msgs_by_table:
                for field in self.settings_by_table[msg_table]["fields"]:
                    msg_fields.append("'" + str(msg["msg"][field]) + "'")
                msg_string = ", ".join(msg_fields)
                msgs_by_table[msg_table].append(msg_string)
        for table, msgs_arr in msgs_by_table.items():
            if len(msgs_arr):
                self.push_msgs(table, msgs_arr)

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=30),
        stop=stop_after_delay(120),
        retry=retry_if_exception_type(ServerException),
    )
    def push_msgs(self, table: str, msgs: list):
        values = [
            "(generateUUIDv4()," + single_msg + ")" for single_msg in msgs
        ]
        config = self.settings_by_table[table]["fields"].keys()
        sq = (
            "INSERT INTO analytic."
            + table
            + " (id, "
            + ", ".join(config)
            + ") VALUES "
            + ", ".join(values)
        )
        self.client.execute(sq)
