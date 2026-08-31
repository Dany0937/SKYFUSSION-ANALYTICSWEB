import { Router } from 'express';
import { PipelineController } from '../../controllers/pipelineController.js';

const router = Router();

router.post('/start', PipelineController.startPipeline);
router.get('/status/:id', PipelineController.getPipelineStatus);
router.get('/list', PipelineController.listPipelines);
router.get('/agents', PipelineController.getAgentStatus);

router.get('/scenes/:zoneId', PipelineController.getScenes);
router.get('/scenes/:zoneId/latest', PipelineController.getLatestScenes);

router.get('/predictions/:zoneId', PipelineController.getPredictions);

router.get('/reports/:zoneId', PipelineController.getReports);
router.get('/reports/:zoneId/latest', PipelineController.getLatestReport);

export default router;
