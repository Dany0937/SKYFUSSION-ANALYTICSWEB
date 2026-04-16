import { EventEmitter } from 'events';
import { createLogger } from '../services/backend-node/src/utils/logger.js';

const logger = createLogger('agent:orchestrator');

export class AgentOrchestrator extends EventEmitter {
  constructor() {
    super();
    this.agents = new Map();
    this.skills = new Map();
  }

  registerAgent(name, agent) {
    this.agents.set(name, {
      ...agent,
      status: 'idle',
      registeredAt: new Date().toISOString()
    });
    logger.info(`Agent registered: ${name}`);
  }

  registerSkill(name, skill) {
    this.skills.set(name, skill);
    logger.info(`Skill registered: ${name}`);
  }

  async executeTask(task) {
    const { agent, skill, payload } = task;
    
    const agentInstance = this.agents.get(agent);
    if (!agentInstance) {
      throw new Error(`Agent not found: ${agent}`);
    }

    const skillInstance = this.skills.get(skill);
    if (!skillInstance) {
      throw new Error(`Skill not found: ${skill}`);
    }

    logger.info(`Executing task`, { agent, skill });

    return {
      success: true,
      result: null,
      metadata: {
        agent,
        skill,
        executedAt: new Date().toISOString()
      }
    };
  }

  getStatus() {
    return {
      agents: Array.from(this.agents.entries()).map(([name, agent]) => ({
        name,
        status: agent.status,
        registeredAt: agent.registeredAt
      })),
      skills: Array.from(this.skills.keys()),
      uptime: process.uptime()
    };
  }
}

export const orchestrator = new AgentOrchestrator();
