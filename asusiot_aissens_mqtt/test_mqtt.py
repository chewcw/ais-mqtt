import signal
import sys
import time
from typing import List

from asusiot_aissens_mqtt.mqtt_config import MQTTConfig
from asusiot_aissens_mqtt.mqtt_consumer import MQTTConsumer
from asusiot_aissens_mqtt.mqtt_producer import MQTTProducer

# Store received messages for verification
received_messages: List[tuple[str, bytes]] = []

def on_message(topic: str, payload: bytes) -> None:
    """Callback function for received messages"""
    print(f"Received message on topic '{topic}': {payload.decode()}")
    received_messages.append((topic, payload))

def main():
    # Create configuration for both producer and consumer
    producer_config = MQTTConfig(
        broker="localhost",
        topic="test/topic",
        qos=1,
        client_id="test_producer"
    )

    consumer_config = MQTTConfig(
        broker="localhost",
        topic="test/topic",
        qos=1,
        client_id="test_consumer"
    )

    # Initialize producer and consumer
    producer = MQTTProducer(producer_config)
    consumer = MQTTConsumer(consumer_config)

    # Set up message callback for consumer
    consumer.set_message_callback(on_message)

    # Connect and start both clients
    try:
        # Start consumer first
        print("Starting consumer...")
        consumer.connect()
        consumer.start()

        # Wait a bit for consumer to connect
        time.sleep(1)

        # Start producer
        print("Starting producer...")
        producer.connect()
        producer.start()

        # Wait a bit for producer to connect
        time.sleep(1)

        # Send test messages
        test_messages = [
            "Hello, MQTT!",
            "This is a test message",
            "Testing 1, 2, 3..."
            "Goodbye!",
            "End of test",
            "This is the end",
            "Or is it?",
            "Yes, it is",
            "No, it's not!",
            "...",
            "Ok, now it is",
            "Bye!",
            "Goodbye!",
            "Goodbye!",
            "Goodbye!",
        ]

        print("\nSending test messages...")
        for msg in test_messages:
            producer.publish(payload=msg)
            print(f"Published: {msg}")
            time.sleep(1)  # Wait between messages

        # Wait a bit to receive all messages
        time.sleep(2)

        # Verify received messages
        print("\nVerifying messages...")
        for i, (topic, payload) in enumerate(received_messages):
            print(f"Message {i + 1}:")
            print(f"  Topic: {topic}")
            print(f"  Payload: {payload.decode()}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean up
        print("Stopping producer and consumer...")
        producer.stop()
        consumer.stop()

def signal_handler(sig, frame):
    print("\nExiting...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()
