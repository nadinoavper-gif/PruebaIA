from __future__ import annotations


def build_hybrid_model(seq_len: int = 128, n_features: int = 24, emb_dim: int = 256):
    from tensorflow.keras import Model, layers

    seq_in = layers.Input((seq_len, n_features), name="seq_features")
    emb_in = layers.Input((emb_dim,), name="visual_embedding")

    emb_seq = layers.RepeatVector(seq_len)(emb_in)
    x = layers.Concatenate()([seq_in, emb_seq])

    x = layers.Bidirectional(layers.GRU(128, return_sequences=True))(x)
    attn = layers.MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    x = layers.LayerNormalization()(x + attn)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(128, activation="gelu")(x)
    x = layers.Dropout(0.2)(x)

    signal = layers.Dense(3, activation="softmax", name="signal")(x)
    confidence = layers.Dense(1, activation="sigmoid", name="confidence")(x)
    zones = layers.Dense(4, activation="linear", name="zones")(x)

    return Model([seq_in, emb_in], [signal, confidence, zones], name="hybrid_cnn_gru_attn")
