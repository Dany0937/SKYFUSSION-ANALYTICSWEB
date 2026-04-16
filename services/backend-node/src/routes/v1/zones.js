import { Router } from 'express';
import { ZoneController } from '../../controllers/zoneController.js';
import { StationController } from '../../controllers/stationController.js';

const router = Router();

router.post('/', ZoneController.create);
router.get('/', ZoneController.getAll);
router.get('/:id', ZoneController.getById);
router.get('/:id/stations', ZoneController.getStations);
router.post('/:id/stations', ZoneController.addStation);

export default router;
