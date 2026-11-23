import winston from 'winston';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ timestamp, level, message, context, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
    return `[${timestamp}] [${context || 'APP'}] ${level.toUpperCase()}: ${message} ${metaStr}`;
  })
);

export function createLogger(context = 'APP') {
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: logFormat,
    transports: [
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          logFormat
        )
      }),
      new winston.transports.File({
        filename: path.join(__dirname, '../../logs/error.log'),
        level: 'error'
      }),
      new winston.transports.File({
        filename: path.join(__dirname, '../../logs/combined.log')
      })
    ]
  });
}

export const logger = createLogger();
