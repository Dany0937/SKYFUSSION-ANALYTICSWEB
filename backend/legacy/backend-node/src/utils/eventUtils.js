import { eventStore } from '../services/eventBus.js';

export function getRecentEvents(limit = 50) {
  const events = eventStore.getEvents();
  return events.slice(-limit).reverse();
}

export function getEventsByType(eventType, limit = 100) {
  return eventStore.getEvents({ event: eventType }).slice(-limit).reverse();
}

export function getEventsInTimeRange(startDate, endDate) {
  return eventStore.getEvents({
    since: startDate,
    until: endDate
  });
}

export function getEventStats() {
  const events = eventStore.getEvents();
  const stats = {};

  for (const event of events) {
    stats[event.event] = (stats[event.event] || 0) + 1;
  }

  return {
    total: events.length,
    byType: stats,
    timeRange: {
      oldest: events[0]?.recordedAt,
      newest: events[events.length - 1]?.recordedAt
    }
  };
}

export function clearEventHistory() {
  eventStore.clear();
}
