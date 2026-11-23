from typing import Any


class GEEClient:
    def __init__(self, project: str, service_account: str = '', key_path: str = ''):
        self.project = project
        self.service_account = service_account
        self.key_path = key_path
        self._ee = None

    def initialize(self):
        import ee
        if self.service_account and self.key_path:
            credentials = ee.ServiceAccountCredentials(self.service_account, self.key_path)
            ee.Initialize(project=self.project, credentials=credentials)
        else:
            ee.Initialize(project=self.project)
        self._ee = ee

    def query_collection(
        self,
        collection_name: str,
        geometry: dict,
        start_date: str,
        end_date: str,
        cloud_filter: int = 20,
        bands: list[str] | None = None,
    ) -> list[dict]:
        ee = self._ee
        aoi = ee.Geometry.Polygon(geometry.get('coordinates', [[]]))

        collection = (
            ee.ImageCollection(collection_name)
            .filterDate(start_date, end_date)
            .filterBounds(aoi)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_filter))
        )

        size = collection.size().getInfo()
        images = collection.toList(size).getInfo()

        results = []
        for img in images:
            props = img.get('properties', {})
            results.append({
                'id': img.get('id', ''),
                'date': props.get('system:time_start', ''),
                'cloud_pct': props.get('CLOUDY_PIXEL_PERCENTAGE', 0),
                'geometry': img.get('geometry', {}),
                'bands': bands or [],
            })

        return results

    def compute_ndvi(self, image_id: str, nir_band: str = 'B8', red_band: str = 'B4') -> dict:
        ee = self._ee
        image = ee.Image(image_id)
        ndvi = image.normalizedDifference([nir_band, red_band]).rename('NDVI')
        return {'image_id': image_id, 'index': 'NDVI', 'band': 'NDVI'}

    def compute_ndwi(self, image_id: str, green_band: str = 'B3', nir_band: str = 'B8') -> dict:
        ee = self._ee
        image = ee.Image(image_id)
        ndwi = image.normalizedDifference([green_band, nir_band]).rename('NDWI')
        return {'image_id': image_id, 'index': 'NDWI', 'band': 'NDWI'}

    def export_to_drive(self, image_id: str, description: str, folder: str, region: dict, scale: int = 10):
        ee = self._ee
        image = ee.Image(image_id)
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder=folder,
            scale=scale,
            region=region,
            maxPixels=1e13,
        )
        task.start()
        return {'task_id': task.id, 'description': description}

    def export_to_cloud_storage(
        self, image_id: str, description: str,
        bucket: str, path: str, region: dict, scale: int = 10,
    ):
        ee = self._ee
        image = ee.Image(image_id)
        task = ee.batch.Export.image.toCloudStorage(
            image=image,
            description=description,
            bucket=bucket,
            fileNamePrefix=path,
            scale=scale,
            region=region,
            maxPixels=1e13,
        )
        task.start()
        return {'task_id': task.id, 'bucket': bucket, 'path': path}
