import json
from multiprocessing import Process

from kafka import KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from settings import settings


def kafka_consume(
    topic: str,
    writer_class,
    topic_settings: dict,
):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[settings.kafka.host + ":" + settings.kafka.port],
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id=topic,
    )
    messages_list = []
    writer = writer_class()
    for message in consumer:
        messages_list.append(
            {
                "table": topic_settings["table"],
                "msg": message.value,
            },
        )

        if len(messages_list) >= 1000:
            writer.write(messages_list)
            messages_list = []
        consumer.commit()

    return True


def start_up():
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=settings.kafka.host + ":" + settings.kafka.port,
            api_version=(0, 9),
        )

        topic_list = []
        topic_list_exists = admin_client.list_topics()
        for model_tuple in settings.topics:
            model = model_tuple[1]
            if not model["topic"] in topic_list_exists:
                topic_list.append(
                    NewTopic(
                        name=model["topic"],
                        num_partitions=3,
                        replication_factor=2,
                    ),
                )
        if len(topic_list):
            admin_client.create_topics(
                new_topics=topic_list,
                validate_only=False,
            )
        return True
    except:
        return False


class KafkaConsumerWrapper:

    def __init__(
        self,
        writer_class,
    ):
        self.writer_class = writer_class

    def kafka_consume_topics(self):
        for model_tuple in settings.topics:
            model = model_tuple[1]
            proc = Process(
                target=kafka_consume,
                kwargs={
                    "topic": model["topic"],
                    "writer_class": self.writer_class,
                    "topic_settings": model,
                },
            )
            proc.start()
