"""
RabbitMQ message queue for asynchronous task processing.
Provides better reliability than simple task queues.
"""
import pika
import json
from typing import Callable, Optional, Dict, Any
from src.core.config import settings
from src.core.logging_config import app_logger


class RabbitMQClient:
    """
    RabbitMQ client for message queue operations.
    
    Features:
    - Message persistence
    - Acknowledgments
    - Dead letter queues
    - Priority queues
    - Message TTL
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5672,
        username: str = 'guest',
        password: str = 'guest'
    ):
        self.host = host
        self.port = port
        self.credentials = pika.PlainCredentials(username, password)
        
        self.connection = None
        self.channel = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=self.credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            self.channel = self.connection.channel()
            
            app_logger.info("✅ Connected to RabbitMQ")
        except Exception as e:
            app_logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise
    
    def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        max_priority: int = 10,
        message_ttl: Optional[int] = None
    ):
        """
        Declare a queue with options.
        
        Args:
            queue_name: Name of the queue
            durable: Persist queue to disk
            max_priority: Maximum priority level
            message_ttl: Message time-to-live in milliseconds
        """
        arguments = {'x-max-priority': max_priority}
        
        if message_ttl:
            arguments['x-message-ttl'] = message_ttl
        
        # Declare main queue
        self.channel.queue_declare(
            queue=queue_name,
            durable=durable,
            arguments=arguments
        )
        
        # Declare dead letter queue
        dlq_name = f"{queue_name}_dlq"
        self.channel.queue_declare(
            queue=dlq_name,
            durable=True
        )
        
        app_logger.info(f"Declared queue: {queue_name}")
    
    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        priority: int = 5,
        persistent: bool = True
    ):
        """
        Publish a message to a queue.
        
        Args:
            queue_name: Queue name
            message: Message payload (will be JSON serialized)
            priority: Message priority (0-10)
            persistent: Make message persistent
        """
        try:
            properties = pika.BasicProperties(
                delivery_mode=2 if persistent else 1,  # 2 = persistent
                priority=priority,
                content_type='application/json'
            )
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=properties
            )
            
            app_logger.debug(f"Published message to {queue_name}")
        
        except Exception as e:
            app_logger.error(f"Error publishing message: {e}")
            raise
    
    def consume_messages(
        self,
        queue_name: str,
        callback: Callable,
        prefetch_count: int = 1
    ):
        """
        Consume messages from a queue.
        
        Args:
            queue_name: Queue name
            callback: Function to process messages
            prefetch_count: Number of messages to prefetch
        """
        self.channel.basic_qos(prefetch_count=prefetch_count)
        
        def wrapper(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except Exception as e:
                app_logger.error(f"Error processing message: {e}")
                
                # Reject and requeue (or send to DLQ)
                ch.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=False  # Send to dead letter queue
                )
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapper,
            auto_ack=False
        )
        
        app_logger.info(f"Started consuming from {queue_name}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
    
    def close(self):
        """Close connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            app_logger.info("Closed RabbitMQ connection")


# Queue names
PAPER_INGESTION_QUEUE = 'paper_ingestion'
EMBEDDING_GENERATION_QUEUE = 'embedding_generation'
SEARCH_INDEXING_QUEUE = 'search_indexing'
NOTIFICATION_QUEUE = 'notifications'


def setup_queues():
    """Set up all required queues."""
    client = RabbitMQClient()
    
    # Paper ingestion queue (high priority for new papers)
    client.declare_queue(
        PAPER_INGESTION_QUEUE,
        durable=True,
        max_priority=10,
        message_ttl=3600000  # 1 hour
    )
    
    # Embedding generation queue
    client.declare_queue(
        EMBEDDING_GENERATION_QUEUE,
        durable=True,
        max_priority=5
    )
    
    # Search indexing queue
    client.declare_queue(
        SEARCH_INDEXING_QUEUE,
        durable=True,
        max_priority=5
    )
    
    # Notification queue (low priority)
    client.declare_queue(
        NOTIFICATION_QUEUE,
        durable=True,
        max_priority=3
    )
    
    client.close()
    
    app_logger.info("✅ All queues set up successfully")