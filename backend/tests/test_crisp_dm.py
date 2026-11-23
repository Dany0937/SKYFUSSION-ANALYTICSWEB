"""
Unit Tests for CRISP-DM Modules: Interpolation & Linear Regression
==================================================================
Incluye pruebas para series completas y series compactas (max 15 datos).
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "ml_tools"))

from spectral_interpolator import SpectralTemporalInterpolator
from crisp_linear_regression import CrispLinearRegressor

class TestCrispDM(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 60
        dates = pd.date_range("2021-01-01", periods=n, freq="16D")
        t = np.arange(n)
        ndvi = 0.5 + 0.003 * t + 0.1 * np.sin(2 * np.pi * t / 23) + np.random.normal(0, 0.02, n)
        evi = 0.3 + 0.002 * t + 0.08 * np.sin(2 * np.pi * t / 23) + np.random.normal(0, 0.02, n)
        
        self.df = pd.DataFrame({"fecha": dates, "NDVI": ndvi, "EVI": evi})
        self.interpolator = SpectralTemporalInterpolator(date_col="fecha")

    def test_interpolacion_sin_huecos_preserva_longitud(self):
        s_with_nan = self.df["NDVI"].copy()
        s_with_nan.iloc[5:9] = np.nan
        s_interp = self.interpolator.interpolate_series(s_with_nan, method="time", dates=self.df["fecha"])
        
        self.assertEqual(len(s_interp), len(s_with_nan))
        self.assertEqual(s_interp.isna().sum(), 0)
        self.assertTrue(0.0 <= s_interp.min() <= 1.0)
        self.assertTrue(0.0 <= s_interp.max() <= 1.0)

    def test_evaluacion_metodos_interpolacion(self):
        eval_df = self.interpolator.evaluate_methods(self.df["NDVI"], gap_percentage=0.20, gap_block_size=2)
        self.assertTrue("rmse" in eval_df.columns)
        self.assertTrue("mae" in eval_df.columns)
        self.assertGreater(len(eval_df), 0)

    def test_regresion_lineal_fit_evaluate(self):
        df_interp = self.interpolator.interpolate_dataframe(self.df, ["NDVI", "EVI"])
        df_interp["t"] = np.arange(len(df_interp))
        
        X = df_interp[["t", "EVI"]]
        y = df_interp["NDVI"]
        
        reg = CrispLinearRegressor(model_type="multiple", scale_features=True)
        reg.fit(X, y)
        
        metrics = reg.evaluate(X, y)
        self.assertIn("r2", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("diagnostico_residuos", metrics)

    def test_interpolacion_restringida_15_puntos(self):
        # Modo 1: Mes a mes
        df_15m = self.interpolator.resample_to_max_points(
            self.df, max_points=15, mode="mes_a_mes", numeric_cols=["NDVI", "EVI"]
        )
        self.assertLessEqual(len(df_15m), 15)
        self.assertGreater(len(df_15m), 0)
        
        # Simular 2 huecos y comprobar interpolacion
        s_gaps = df_15m["NDVI"].copy()
        s_gaps.iloc[1] = np.nan
        s_gaps.iloc[3] = np.nan
        s_rec = self.interpolator.interpolate_series(s_gaps, method="linear")
        self.assertEqual(s_rec.isna().sum(), 0)
        
        # Modo 2: Año a año
        df_ano = self.interpolator.resample_to_max_points(
            self.df, max_points=15, mode="ano_a_ano", numeric_cols=["NDVI", "EVI"]
        )
        self.assertLessEqual(len(df_ano), 15)
        self.assertGreater(len(df_ano), 0)

if __name__ == "__main__":
    unittest.main()
