import numpy as np

from rnn.preprocess import preparar_datos


def test_preparar_datos_separa_pixeles_sin_solapamiento():
    datos = preparar_datos(
        "data/raw/series_sinteticas_combima.csv",
        timesteps=24,
        horizonte=1,
        guardar_splits=False,
    )

    conjuntos = [
        {tuple(coord) for coord in datos[f"coords_{nombre}"]}
        for nombre in ("train", "val", "test")
    ]

    assert all(datos[f"X_{nombre}"].shape[0] > 0 for nombre in ("train", "val", "test"))
    assert datos["X_train"].shape[1:] == (24, len(datos["feature_cols"]))
    assert datos["y_train"].shape[1] == 1
    assert not (conjuntos[0] & conjuntos[1])
    assert not (conjuntos[0] & conjuntos[2])
    assert not (conjuntos[1] & conjuntos[2])

    train_min = np.min(datos["X_train"], axis=(0, 1))
    train_max = np.max(datos["X_train"], axis=(0, 1))
    assert np.all(train_min >= 0.0)
    assert np.all(train_max <= 1.0)