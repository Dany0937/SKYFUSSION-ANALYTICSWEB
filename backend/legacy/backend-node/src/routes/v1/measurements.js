import { Router } from 'express';
import { MeasurementController } from '../../controllers/measurementController.js';

const router = Router();

router.post('/years', MeasurementController.createYear);
router.get('/years', MeasurementController.getAllYears);
router.get('/years/:id', MeasurementController.getYearById);
router.get('/years/:anoId/measurements', MeasurementController.getMeasurements);
router.get('/years/:anoId/measurements/range', MeasurementController.getMeasurementsByDateRange);
router.get('/years/:anoId/statistics', MeasurementController.getStatistics);

router.post('/ingest', MeasurementController.ingestMeasurement);
router.post('/ingest/batch', MeasurementController.ingestBatch);
router.get('/buffer/status', MeasurementController.getBufferStatus);

export default router;
