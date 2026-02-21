from __future__ import annotations


def build_temporal_model(seq_len: int = 128, n_features: int = 24):
    from tensorflow.keras import Model, layers

    x_in = layers.Input((seq_len, n_features), name="temporal_features")
    x = layers.Bidirectional(layers.GRU(128, return_sequences=True))(x_in)
    attn = layers.MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    x = layers.LayerNormalization()(x + attn)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(128, activation="gelu")(x)
    x = layers.Dropout(0.2)(x)

    direction = layers.Dense(3, activation="softmax", name="direction")(x)
    horizon = layers.Dense(1, activation="relu", name="horizon")(x)
    return Model(x_in, [direction, horizon], name="temporal_attn_model")
