import { Router } from 'express';
import zonesRouter from './v1/zones.js';
import measurementsRouter from './v1/measurements.js';
import stationsRouter from './v1/stations.js';
import alertsRouter from './v1/alerts.js';

const router = Router();

router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

router.use('/zones', zonesRouter);
router.use('/measurements', measurementsRouter);
router.use('/stations', stationsRouter);
router.use('/alerts', alertsRouter);

export default router;
