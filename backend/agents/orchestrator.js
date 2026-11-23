import { EventEmitter } from 'events';
import { spawn } from 'child_process';
import { createLogger } from '../services/backend-node/src/utils/logger.js';
import { eventBus, EVENTS } from '../services/backend-node/src/services/eventBus.js';

const logger = createLogger('agent:orchestrator');

const PYTHON_AGENTS_MAP = {
  geospatial: { script: 'geospatial_agent/agent.py', event: EVENTS.ANALYSIS_REQUESTED },
  vision: { script: 'vision_agent/agent.py', event: EVENTS.DATA_INGESTED },
  oracle: { script: 'oracle_agent/agent.py', event: EVENTS.ANALYSIS_COMPLETED },
  reporting: { script: 'reporting_agent/agent.py', event: EVENTS.PREDICTION_COMPLETED },
};

export class AgentOrchestrator extends EventEmitter {
  constructor() {
    super();
    this.agents = new Map();
    this.skills = new Map();
    this.pythonProcesses = new Map();
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

  async startPythonAgent(agentName) {
    const config = PYTHON_AGENTS_MAP[agentName];
    if (!config) {
      throw new Error(`Unknown Python agent: ${agentName}`);
    }

    const scriptPath = new URL(`python/${config.script}`, import.meta.url).pathname;
    const proc = spawn('python', [scriptPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONPATH: 'agents/python' }
    });

    proc.stdout.on('data', (data) => {
      try {
        const msg = JSON.parse(data.toString().trim());
        logger.info(`[${agentName}] ${msg.message || data.toString().trim()}`);
        if (msg.event) {
          eventBus.publish(msg.event, msg.payload);
        }
      } catch {
        logger.info(`[${agentName}] ${data.toString().trim()}`);
      }
    });

    proc.stderr.on('data', (data) => {
      logger.error(`[${agentName}] ${data.toString().trim()}`);
    });

    proc.on('close', (code) => {
      logger.warn(`[${agentName}] exited with code ${code}`);
      this.pythonProcesses.delete(agentName);
    });

    this.pythonProcesses.set(agentName, proc);
    logger.info(`Python agent started: ${agentName}`);
    return proc;
  }

  startAllPythonAgents() {
    return Promise.all(
      Object.keys(PYTHON_AGENTS_MAP).map(name => this.startPythonAgent(name))
    );
  }

  stopPythonAgent(agentName) {
    const proc = this.pythonProcesses.get(agentName);
    if (proc) {
      proc.kill('SIGTERM');
      this.pythonProcesses.delete(agentName);
      logger.info(`Python agent stopped: ${agentName}`);
    }
  }

  stopAllPythonAgents() {
    for (const name of this.pythonProcesses.keys()) {
      this.stopPythonAgent(name);
    }
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

  async orchestratePipeline(geometry, startDate, endDate) {
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    logger.info(`Starting pipeline [${requestId}]`, { geometry, startDate, endDate });

    eventBus.publish(EVENTS.ANALYSIS_REQUESTED, {
      request_id: requestId,
      geometry,
      start_date: startDate,
      end_date: endDate,
      collections: ['S2', 'L8'],
    });

    return { requestId, status: 'pipeline_started' };
  }

  getStatus() {
    return {
      agents: Array.from(this.agents.entries()).map(([name, agent]) => ({
        name,
        status: agent.status,
        registeredAt: agent.registeredAt
      })),
      pythonAgents: Array.from(this.pythonProcesses.keys()),
      skills: Array.from(this.skills.keys()),
      uptime: process.uptime()
    };
  }
}

export const orchestrator = new AgentOrchestrator();
