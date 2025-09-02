import gc

from clickhouse_writer import ClickhouseWriter, ping
from kafka_consumer_wrapper import KafkaConsumerWrapper, start_up

if __name__ == "__main__":
    gc.enable()
    gc.set_debug(gc.DEBUG_STATS)
    gc.set_threshold(2000)
    writer = ClickhouseWriter()
    while True:
        if ping():
            break
    writer.start_up()
    kafka_consumer_wrapper = KafkaConsumerWrapper(
        ClickhouseWriter,
    )
    while True:
        if start_up():
            break
    kafka_consumer_wrapper.kafka_consume_topics()
