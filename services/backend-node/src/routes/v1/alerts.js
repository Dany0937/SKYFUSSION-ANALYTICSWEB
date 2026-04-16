import { Router } from 'express';
import { AlertController } from '../../controllers/alertController.js';

const router = Router();

router.post('/classify', AlertController.classifyAlert);
router.get('/active', AlertController.getActiveAlerts);
router.get('/history', AlertController.getAlertHistory);
router.patch('/:id/acknowledge', AlertController.acknowledgeAlert);
router.delete('/:id/resolve', AlertController.resolveAlert);

export default router;
