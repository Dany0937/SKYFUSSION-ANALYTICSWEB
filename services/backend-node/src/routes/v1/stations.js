import { Router } from 'express';
import { StationController } from '../../controllers/stationController.js';

const router = Router();

router.post('/', StationController.create);
router.get('/', StationController.getAll);
router.get('/nearby', StationController.findNearby);
router.get('/:id', StationController.getById);
router.get('/zone/:zoneId', StationController.findByZone);
router.patch('/:id/status', StationController.updateStatus);

export default router;
