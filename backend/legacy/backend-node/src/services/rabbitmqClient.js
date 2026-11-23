import amqp from 'amqplib';
import { EventEmitter } from 'events';
import { createLogger } from '../utils/logger.js';
import { eventBus, EVENTS } from './eventBus.js';

const logger = createLogger('services:rabbitmq');

export const AGENT_EVENTS = {
  ANALYSIS_REQUESTED: 'analysis:requested',
  DATA_INGESTED: 'data:ingested',
  IMAGERY_PROCESSED: 'imagery:processed',
  PREDICTION_REQUESTED: 'prediction:requested',
  PREDICTION_COMPLETED: 'prediction:completed',
  REPORT_GENERATED: 'report:generated',
  AGENT_HEARTBEAT: 'agent:heartbeat',
  AGENT_ERROR: 'agent:error'
};

const RABBITMQ_EVENT_MAP = {
  [EVENTS.ANALYSIS_REQUESTED]: AGENT_EVENTS.ANALYSIS_REQUESTED,
  [EVENTS.DATA_INGESTED]: AGENT_EVENTS.DATA_INGESTED,
  [EVENTS.PREDICTION_REQUESTED]: AGENT_EVENTS.PREDICTION_REQUESTED,
  [EVENTS.PREDICTION_COMPLETED]: AGENT_EVENTS.PREDICTION_COMPLETED,
  [EVENTS.REPORT_READY]: AGENT_EVENTS.REPORT_GENERATED
};

export class RabbitMQClient extends EventEmitter {
  constructor() {
    super();
    this.connection = null;
    this.channel = null;
    this.reconnectAttempts = 0;
    this.consumers = new Map();
    this.isConnected = false;

    this.config = {
      host: process.env.RABBITMQ_HOST || 'localhost',
      port: parseInt(process.env.RABBITMQ_PORT, 10) || 5672,
      user: process.env.RABBITMQ_USER || 'skyfusion',
      pass: process.env.RABBITMQ_PASS || 'skyfusion_secure_pass',
      vhost: process.env.RABBITMQ_VHOST || '/',
      exchange: process.env.RABBITMQ_EXCHANGE || 'skyfusion.events',
      heartbeat: parseInt(process.env.RABBITMQ_HEARTBEAT, 10) || 60,
      reconnectDelay: parseInt(process.env.RABBITMQ_RECONNECT_DELAY_MS, 10) || 5000,
      maxReconnect: parseInt(process.env.RABBITMQ_MAX_RECONNECT_ATTEMPTS, 10) || 10
    };
  }

  async connect() {
    try {
      const url = `amqp://${this.config.user}:${this.config.pass}@${this.config.host}:${this.config.port}${this.config.vhost}`;

      this.connection = await amqp.connect(url, {
        heartbeat: this.config.heartbeat
      });

      this.connection.on('close', () => {
        this.isConnected = false;
        logger.warn('RabbitMQ connection closed');
        this.scheduleReconnect();
      });

      this.connection.on('error', (err) => {
        this.isConnected = false;
        logger.error('RabbitMQ connection error', { error: err.message });
        this.scheduleReconnect();
      });

      this.channel = await this.connection.createChannel();

      await this.channel.assertExchange(this.config.exchange, 'topic', {
        durable: true,
        autoDelete: false
      });

      this.isConnected = true;
      this.reconnectAttempts = 0;
      logger.info('RabbitMQ connected', { host: this.config.host, exchange: this.config.exchange });

      this.bindInternalBridge();

      return true;
    } catch (error) {
      this.isConnected = false;
      logger.error('RabbitMQ connection failed', { error: error.message });
      this.scheduleReconnect();
      return false;
    }
  }

  bindInternalBridge() {
    Object.entries(RABBITMQ_EVENT_MAP).forEach(([internalEvent, rabbitEvent]) => {
      eventBus.on(internalEvent, (data) => {
        this.publish(rabbitEvent, data).catch(err => {
          logger.error('Bridge publish failed', { event: rabbitEvent, error: err.message });
        });
      });
    });

    Object.values(AGENT_EVENTS).forEach((agentEvent) => {
      this.on(agentEvent, (data) => {
        const mappedEvent = Object.entries(RABBITMQ_EVENT_MAP)
          .find(([, v]) => v === agentEvent)?.[0];

        if (mappedEvent) {
          eventBus.emit(mappedEvent, data);
        }
      });
    });
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.config.maxReconnect) {
      logger.error('Max RabbitMQ reconnection attempts reached');
      this.emit('max_reconnect_exceeded');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectDelay * Math.min(this.reconnectAttempts, 5);

    logger.info('Scheduling RabbitMQ reconnection', {
      attempt: this.reconnectAttempts,
      delay
    });

    setTimeout(() => this.connect(), delay);
  }

  async publish(event, payload) {
    if (!this.isConnected) {
      logger.warn('RabbitMQ not connected, event queued in memory', { event });
      this.emit(event, payload);
      return false;
    }

    try {
      const message = {
        event,
        payload: {
          ...payload,
          publishedAt: new Date().toISOString()
        },
        metadata: {
          source: 'backend',
          version: '1.0'
        }
      };

      const buffer = Buffer.from(JSON.stringify(message));

      this.channel.publish(this.config.exchange, event, buffer, {
        persistent: true,
        contentType: 'application/json',
        timestamp: Date.now()
      });

      logger.debug('Event published to RabbitMQ', { event, routingKey: event });
      return true;
    } catch (error) {
      logger.error('Failed to publish event', { event, error: error.message });
      return false;
    }
  }

  async subscribe(queueName, routingKey, handler) {
    try {
      const queue = await this.channel.assertQueue(queueName, {
        durable: true,
        autoDelete: false
      });

      await this.channel.bindQueue(queue.queue, this.config.exchange, routingKey);

      const consumerTag = await this.channel.consume(queue.queue, async (msg) => {
        if (!msg) return;

        try {
          const content = JSON.parse(msg.content.toString());
          const startTime = Date.now();

          await handler(content);

          this.channel.ack(msg);

          logger.debug('Event processed', {
            routingKey,
            duration: Date.now() - startTime
          });
        } catch (error) {
          logger.error('Event processing failed', {
            routingKey,
            error: error.message
          });

          if (msg.fields.redelivered) {
            this.channel.nack(msg, false, false);
          } else {
            this.channel.nack(msg, false, true);
          }
        }
      });

      this.consumers.set(routingKey, { queue: queue.queue, consumerTag });

      logger.info('Subscribed to events', { queue: queue.queue, routingKey });
      return consumerTag;
    } catch (error) {
      logger.error('Failed to subscribe', { queue: queueName, routingKey, error: error.message });
      throw error;
    }
  }

  async unsubscribe(routingKey) {
    const consumer = this.consumers.get(routingKey);
    if (consumer) {
      await this.channel.cancel(consumer.consumerTag);
      this.consumers.delete(routingKey);
      logger.info('Unsubscribed from events', { routingKey });
    }
  }

  async getQueueInfo(queueName) {
    try {
      const info = await this.channel.checkQueue(queueName);
      return {
        name: queueName,
        messageCount: info.messageCount,
        consumerCount: info.consumerCount
      };
    } catch (error) {
      logger.error('Failed to get queue info', { queue: queueName, error: error.message });
      return null;
    }
  }

  async disconnect() {
    try {
      for (const [routingKey] of this.consumers) {
        await this.unsubscribe(routingKey);
      }

      if (this.channel) {
        await this.channel.close();
      }

      if (this.connection) {
        await this.connection.close();
      }

      this.isConnected = false;
      logger.info('RabbitMQ disconnected');
    } catch (error) {
      logger.error('Error during RabbitMQ disconnect', { error: error.message });
    }
  }
}

export const rabbitMQClient = new RabbitMQClient();
export default rabbitMQClient;
