# Optional extension. Install kafka-python and configure a broker/topic before use.
def main():
    try:
        from kafka import KafkaConsumer
    except ImportError as exc:
        raise SystemExit("Install optional dependency: pip install kafka-python") from exc
    consumer = KafkaConsumer("sentinelguard-transactions",
        bootstrap_servers=["localhost:9092"],
        value_deserializer=lambda value: value.decode("utf-8"))
    for message in consumer:
        print("Received event:", message.value)
        # Connect this consumer to validation + inference after configuring your broker.

if __name__ == "__main__":
    main()
