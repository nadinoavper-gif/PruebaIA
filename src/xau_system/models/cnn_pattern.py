from __future__ import annotations


def build_cnn(input_shape=(224, 224, 3), n_patterns: int = 10):
    import tensorflow as tf
    from tensorflow.keras import Model, layers

    x_in = layers.Input(shape=input_shape, name="candles_image")
    x = x_in
    for filters in [32, 64, 128, 256]:
        x = layers.Conv2D(filters, 3, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        if filters < 256:
            x = layers.MaxPool2D(2)(x)

    emb = layers.GlobalAveragePooling2D(name="embedding")(x)
    pattern = layers.Dense(n_patterns, activation="softmax", name="pattern_head")(emb)
    quality = layers.Dense(1, activation="sigmoid", name="quality_head")(emb)
    breakout = layers.Dense(1, activation="sigmoid", name="breakout_head")(emb)
    return Model(x_in, [pattern, quality, breakout, emb], name="cnn_pattern")


def compile_cnn(model, lr: float = 1e-3):
    import tensorflow as tf

    losses = {
        "pattern_head": tf.keras.losses.CategoricalFocalCrossentropy(),
        "quality_head": tf.keras.losses.BinaryCrossentropy(),
        "breakout_head": tf.keras.losses.BinaryCrossentropy(),
    }
    model.compile(optimizer=tf.keras.optimizers.Adam(lr), loss=losses)
    return model
