"""
Data Preprocessing Module for Caudal Prediction
===============================================

Funciones de preprocesamiento para datos de series temporales:
- Carga de datos desde CSV
- Normalización con MinMaxScaler
- Creación de secuencias para LSTM
- Merge de múltiples fuentes de datos (caudal, precipitación, ancho río)
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class PreprocessedData:
    """Contenedor para datos preprocesados listos para el modelo."""
    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    scalers: Dict[str, MinMaxScaler]
    feature_columns: List[str]
    target_column: str
    sequence_length: int


class TemporalDataPreprocessor:
    """
    Preprocesador de datos temporales para modelos LSTM.
    
    Maneja:
    - Carga de múltiples fuentes de datos
    - Interpolación de valores faltantes
    - Normalización multivariada
    - Creación de secuencias temporales
    """

    def __init__(
        self,
        sequence_length: int = 72,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> None:
        """
        Inicializa el preprocesador.
        
        Args:
            sequence_length: Número de pasos temporales para cada secuencia
            train_ratio: Proporción de datos para entrenamiento
            val_ratio: Proporción de datos para validación
            test_ratio: Proporción de datos para prueba
        """
        if not (0 < train_ratio < 1) or not (0 < val_ratio < 1) or not (0 < test_ratio < 1):
            raise ValueError("Las proporciones deben estar entre 0 y 1")
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
            raise ValueError("Las proporciones deben sumar 1.0")
            
        self.sequence_length = sequence_length
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        
        self.scalers: Dict[str, MinMaxScaler] = {}
        self.feature_columns: List[str] = []
        self.target_column: str = "caudal_m3s"
        self.dataframe: Optional[pd.DataFrame] = None

    def load_csv(
        self,
        file_path: str,
        date_column: str = "fecha",
        parse_dates: bool = True
    ) -> pd.DataFrame:
        """
        Carga datos desde archivo CSV.
        
        Args:
            file_path: Ruta al archivo CSV
            date_column: Nombre de la columna de fecha
            parse_dates: Si debe parsear las fechas
            
        Returns:
            DataFrame con los datos cargados
        """
        try:
            if parse_dates:
                self.dataframe = pd.read_csv(
                    file_path,
                    parse_dates=[date_column] if date_column else None,
                    infer_datetime_format=True
                )
                if date_column and date_column in self.dataframe.columns:
                    self.dataframe.set_index(date_column, inplace=True)
                    self.dataframe.sort_index(inplace=True)
            else:
                self.dataframe = pd.read_csv(file_path)
                
            return self.dataframe
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error cargando CSV: {str(e)}")

    def merge_datasets(
        self,
        caudal_df: pd.DataFrame,
        precipitacion_df: pd.DataFrame,
        river_width_df: Optional[pd.DataFrame] = None,
        merge_how: str = "inner"
    ) -> pd.DataFrame:
        """
        Combina múltiples fuentes de datos en un solo DataFrame.
        
        Args:
            caudal_df: DataFrame con datos de caudal
            precipitacion_df: DataFrame con datos de precipitación
            river_width_df: DataFrame opcional con datos de ancho del río
            merge_how: Tipo de merge ('inner', 'outer', 'left', 'right')
            
        Returns:
            DataFrame combinado
        """
        if merge_how not in ["inner", "outer", "left", "right"]:
            raise ValueError(f"Tipo de merge no válido: {merge_how}")
            
        result = caudal_df.copy()
        
        precip_renamed = precipitacion_df.rename(
            columns={col: f"precipitacion_{col}" for col in precipitacion_df.columns}
        )
        result = result.join(precip_renamed, how=merge_how)
        
        if river_width_df is not None:
            width_renamed = river_width_df.rename(
                columns={col: f"ancho_rio_{col}" for col in river_width_df.columns}
            )
            result = result.join(width_renamed, how=merge_how)
            
        self.dataframe = result
        return result

    def handle_missing_values(
        self,
        method: str = "interpolate",
        fill_value: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Maneja valores faltantes en el DataFrame.
        
        Args:
            method: 'interpolate', 'forward_fill', 'backward_fill', 'fill_value'
            fill_value: Valor a usar si method='fill_value'
            
        Returns:
            DataFrame sin valores faltantes
        """
        if self.dataframe is None:
            raise RuntimeError("No hay datos cargados. Use load_csv() primero.")
            
        df = self.dataframe.copy()
        
        original_missing = df.isnull().sum().sum()
        
        if method == "interpolate":
            df = df.interpolate(method="time")
            df = df.fillna(method="bfill").fillna(method="ffill")
            
        elif method == "forward_fill":
            df = df.fillna(method="ffill")
            
        elif method == "backward_fill":
            df = df.fillna(method="bfill")
            
        elif method == "fill_value":
            df = df.fillna(fill_value if fill_value is not None else 0)
            
        else:
            raise ValueError(f"Método no reconocido: {method}")
            
        final_missing = df.isnull().sum().sum()
        
        self.dataframe = df
        
        return df

    def select_features(
        self,
        feature_columns: List[str],
        target_column: str
    ) -> None:
        """
        Selecciona las columnas para características y objetivo.
        
        Args:
            feature_columns: Lista de columnas de entrada
            target_column: Columna objetivo a predecir
        """
        if self.dataframe is None:
            raise RuntimeError("No hay datos cargados")
            
        missing_features = [c for c in feature_columns if c not in self.dataframe.columns]
        if missing_features:
            raise ValueError(f"Columnas no encontradas: {missing_features}")
            
        if target_column not in self.dataframe.columns:
            raise ValueError(f"Columna objetivo no encontrada: {target_column}")
            
        self.feature_columns = feature_columns
        self.target_column = target_column

    def normalize(
        self,
        method: str = "minmax"
    ) -> None:
        """
        Normaliza las columnas seleccionadas.
        
        Args:
            method: 'minmax' para MinMaxScaler o 'standard' para StandardScaler
        """
        if self.dataframe is None:
            raise RuntimeError("No hay datos cargados")
            
        if not self.feature_columns:
            raise RuntimeError("Use select_features() primero")
            
        all_columns = self.feature_columns + [self.target_column]
        
        for col in all_columns:
            if method == "minmax":
                scaler = MinMaxScaler()
            elif method == "standard":
                scaler = StandardScaler()
            else:
                raise ValueError(f"Método de normalización no válido: {method}")
                
            self.dataframe[f"{col}_scaled"] = scaler.fit_transform(
                self.dataframe[[col]]
            )
            self.scalers[col] = scaler

    def create_sequences(
        self,
        X_data: np.ndarray,
        y_data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea secuencias temporales para entrada LSTM.
        
        Args:
            X_data: Array de características (n_samples, n_features)
            y_data: Array de objetivos (n_samples,)
            
        Returns:
            Tupla de arrays de secuencias (X_seq, y_seq)
        """
        X_sequences: List[np.ndarray] = []
        y_sequences: List[np.ndarray] = []
        
        for i in range(len(X_data) - self.sequence_length):
            X_sequences.append(X_data[i:i + self.sequence_length])
            y_sequences.append(y_data[i + self.sequence_length])
            
        return np.array(X_sequences), np.array(y_sequences)

    def prepare_data(
        self,
        feature_columns: Optional[List[str]] = None,
        target_column: Optional[str] = None
    ) -> PreprocessedData:
        """
        Prepara los datos completos para entrenamiento.
        
        Args:
            feature_columns: Lista de columnas de características
            target_column: Columna objetivo
            
        Returns:
            Objeto PreprocessedData con todos los sets
        """
        if self.dataframe is None:
            raise RuntimeError("No hay datos cargados")
            
        if feature_columns:
            self.feature_columns = feature_columns
        if target_column:
            self.target_column = target_column
            
        if not self.feature_columns:
            raise RuntimeError("Debe especificar feature_columns")
            
        scaled_features = [f"{col}_scaled" for col in self.feature_columns]
        scaled_target = f"{self.target_column}_scaled"
        
        X = self.dataframe[scaled_features].values
        y = self.dataframe[scaled_target].values
        
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y,
            test_size=self.test_ratio,
            shuffle=False
        )
        
        val_size = self.val_ratio / (self.train_ratio + self.val_ratio)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val,
            test_size=val_size,
            shuffle=False
        )
        
        X_train_seq, y_train_seq = self.create_sequences(X_train, y_train)
        X_val_seq, y_val_seq = self.create_sequences(X_val, y_val)
        X_test_seq, y_test_seq = self.create_sequences(X_test, y_test)
        
        return PreprocessedData(
            X_train=X_train_seq,
            y_train=y_train_seq,
            X_val=X_val_seq,
            y_val=y_val_seq,
            X_test=X_test_seq,
            y_test=y_test_seq,
            scalers=self.scalers,
            feature_columns=self.feature_columns,
            target_column=self.target_column,
            sequence_length=self.sequence_length
        )

    def inverse_transform_target(
        self,
        scaled_values: np.ndarray
    ) -> np.ndarray:
        """
        Desnormaliza valores predichos.
        
        Args:
            scaled_values: Valores normalizados
            
        Returns:
            Valores en escala original
        """
        if self.target_column not in self.scalers:
            raise RuntimeError(f"No se encontró scaler para {self.target_column}")
            
        scaler = self.scalers[self.target_column]
        return scaler.inverse_transform(
            scaled_values.reshape(-1, 1)
        ).flatten()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del dataset.
        
        Returns:
            Diccionario con estadísticas
        """
        if self.dataframe is None:
            return {}
            
        return {
            "total_samples": len(self.dataframe),
            "date_range": {
                "start": str(self.dataframe.index.min()),
                "end": str(self.dataframe.index.max())
            },
            "features": self.feature_columns,
            "target": self.target_column,
            "missing_values": self.dataframe.isnull().sum().to_dict(),
            "descriptive_stats": self.dataframe[self.feature_columns + [self.target_column]].describe().to_dict()
        }


def load_and_preprocess_demo(
    caudal_csv: str,
    precip_csv: str,
    river_width_csv: Optional[str] = None
) -> PreprocessedData:
    """
    Función de demostración que carga y preprocesa datos.
    
    Args:
        caudal_csv: Ruta a CSV de caudal
        precip_csv: Ruta a CSV de precipitación
        river_width_csv: Ruta opcional a CSV de ancho del río
        
    Returns:
        Objeto PreprocessedData listo para entrenamiento
    """
    preprocessor = TemporalDataPreprocessor(
        sequence_length=72,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    caudal_df = preprocessor.load_csv(caudal_csv)
    precip_df = preprocessor.load_csv(precip_csv)
    
    river_width_df = None
    if river_width_csv:
        river_width_df = preprocessor.load_csv(river_width_csv)
    
    preprocessor.merge_datasets(caudal_df, precip_df, river_width_df)
    preprocessor.handle_missing_values(method="interpolate")
    
    preprocessor.select_features(
        feature_columns=["caudal_m3s", "precipitacion_mm"],
        target_column="caudal_m3s"
    )
    
    preprocessor.normalize(method="minmax")
    
    return preprocessor.prepare_data()
