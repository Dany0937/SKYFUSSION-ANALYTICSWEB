import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { createLogger } from './utils/logger.js';
import { initializeDatabase, closeDatabase } from './config/database.js';
import { validateExternalConfig } from './config/externalApis.js';
import { rabbitMQClient } from './services/rabbitmqClient.js';
import { agentOrchestrator } from './services/agentOrchestrator.js';
import routes from './routes/index.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';
import { rateLimiter } from './middleware/rateLimiter.js';

dotenv.config();

const logger = createLogger('app');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

app.use((req, res, next) => {
  logger.info('Incoming request', {
    method: req.method,
    path: req.path,
    ip: req.ip
  });
  next();
});

app.use(rateLimiter);

app.use('/api/v1', routes);

app.use(notFoundHandler);
app.use(errorHandler);

async function startServer() {
  try {
    await initializeDatabase();
    logger.info('Database initialized successfully');

    validateExternalConfig();

    const connected = await rabbitMQClient.connect();
    if (connected) {
      logger.info('RabbitMQ event bus connected');
    } else {
      logger.warn('RabbitMQ unavailable, using in-process event bridge');
    }

    app.listen(PORT, () => {
      logger.info(`Skyfusion Analytics API running on port ${PORT}`, {
        env: process.env.NODE_ENV,
        port: PORT
      });
    });
  } catch (error) {
    logger.error('Failed to start server', { error: error.message });
    process.exit(1);
  }
}

process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  await agentOrchestrator.shutdown();
  await rabbitMQClient.disconnect();
  await closeDatabase();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully');
  await agentOrchestrator.shutdown();
  await rabbitMQClient.disconnect();
  await closeDatabase();
  process.exit(0);
});

startServer();

export default app;
