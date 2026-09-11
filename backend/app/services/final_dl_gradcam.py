"""Runtime Grad-CAM implementation for the frozen EfficientNet-B0 candidate."""

from __future__ import annotations

import base64
import io
from typing import Tuple, Any

import numpy as np
from PIL import Image

GRADCAM_LAYER = "top_conv"
GRADCAM_METHOD = "Grad-CAM"
GRADCAM_DISCLAIMER = (
    "Grad-CAM shows coarse model-attention regions on the 224x224 input representation. "
    "It is not a validated lesion localization, segmentation, or pathology boundary."
)

# Precomputed 256-level JET colormap lookup table (RGB) matching matplotlib.colormaps['jet'] exactly.
# Decouples runtime Grad-CAM visualization from matplotlib dependency.
JET_LUT = np.array([
    [0, 0, 127], [0, 0, 132], [0, 0, 136], [0, 0, 141], [0, 0, 145], [0, 0, 150], [0, 0, 154], [0, 0, 159],
    [0, 0, 163], [0, 0, 168], [0, 0, 172], [0, 0, 177], [0, 0, 182], [0, 0, 186], [0, 0, 191], [0, 0, 195],
    [0, 0, 200], [0, 0, 204], [0, 0, 209], [0, 0, 213], [0, 0, 218], [0, 0, 222], [0, 0, 227], [0, 0, 232],
    [0, 0, 236], [0, 0, 241], [0, 0, 245], [0, 0, 250], [0, 0, 254], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 4, 255], [0, 8, 255], [0, 12, 255], [0, 16, 255], [0, 20, 255], [0, 24, 255], [0, 28, 255],
    [0, 32, 255], [0, 36, 255], [0, 40, 255], [0, 44, 255], [0, 48, 255], [0, 52, 255], [0, 56, 255], [0, 60, 255],
    [0, 64, 255], [0, 68, 255], [0, 72, 255], [0, 76, 255], [0, 80, 255], [0, 84, 255], [0, 88, 255], [0, 92, 255],
    [0, 96, 255], [0, 100, 255], [0, 104, 255], [0, 108, 255], [0, 112, 255], [0, 116, 255], [0, 120, 255], [0, 124, 255],
    [0, 128, 255], [0, 132, 255], [0, 136, 255], [0, 140, 255], [0, 144, 255], [0, 148, 255], [0, 152, 255], [0, 156, 255],
    [0, 160, 255], [0, 164, 255], [0, 168, 255], [0, 172, 255], [0, 176, 255], [0, 180, 255], [0, 184, 255], [0, 188, 255],
    [0, 192, 255], [0, 196, 255], [0, 200, 255], [0, 204, 255], [0, 208, 255], [0, 212, 255], [0, 216, 255], [0, 220, 254],
    [0, 224, 250], [0, 228, 247], [2, 232, 244], [5, 236, 241], [8, 240, 237], [12, 244, 234], [15, 248, 231], [18, 252, 228],
    [21, 255, 225], [24, 255, 221], [28, 255, 218], [31, 255, 215], [34, 255, 212], [37, 255, 208], [41, 255, 205], [44, 255, 202],
    [47, 255, 199], [50, 255, 195], [54, 255, 192], [57, 255, 189], [60, 255, 186], [63, 255, 183], [66, 255, 179], [70, 255, 176],
    [73, 255, 173], [76, 255, 170], [79, 255, 166], [83, 255, 163], [86, 255, 160], [89, 255, 157], [92, 255, 154], [95, 255, 150],
    [99, 255, 147], [102, 255, 144], [105, 255, 141], [108, 255, 137], [112, 255, 134], [115, 255, 131], [118, 255, 128], [121, 255, 125],
    [124, 255, 121], [128, 255, 118], [131, 255, 115], [134, 255, 112], [137, 255, 108], [141, 255, 105], [144, 255, 102], [147, 255, 99],
    [150, 255, 95], [154, 255, 92], [157, 255, 89], [160, 255, 86], [163, 255, 83], [166, 255, 79], [170, 255, 76], [173, 255, 73],
    [176, 255, 70], [179, 255, 66], [183, 255, 63], [186, 255, 60], [189, 255, 57], [192, 255, 54], [195, 255, 50], [199, 255, 47],
    [202, 255, 44], [205, 255, 41], [208, 255, 37], [212, 255, 34], [215, 255, 31], [218, 255, 28], [221, 255, 24], [224, 255, 21],
    [228, 255, 18], [231, 255, 15], [234, 255, 12], [237, 255, 8], [241, 252, 5], [244, 248, 2], [247, 244, 0], [250, 240, 0],
    [254, 237, 0], [255, 233, 0], [255, 229, 0], [255, 226, 0], [255, 222, 0], [255, 218, 0], [255, 215, 0], [255, 211, 0],
    [255, 207, 0], [255, 203, 0], [255, 200, 0], [255, 196, 0], [255, 192, 0], [255, 189, 0], [255, 185, 0], [255, 181, 0],
    [255, 177, 0], [255, 174, 0], [255, 170, 0], [255, 166, 0], [255, 163, 0], [255, 159, 0], [255, 155, 0], [255, 152, 0],
    [255, 148, 0], [255, 144, 0], [255, 140, 0], [255, 137, 0], [255, 133, 0], [255, 129, 0], [255, 126, 0], [255, 122, 0],
    [255, 118, 0], [255, 115, 0], [255, 111, 0], [255, 107, 0], [255, 103, 0], [255, 100, 0], [255, 96, 0], [255, 92, 0],
    [255, 89, 0], [255, 85, 0], [255, 81, 0], [255, 77, 0], [255, 74, 0], [255, 70, 0], [255, 66, 0], [255, 63, 0],
    [255, 59, 0], [255, 55, 0], [255, 52, 0], [255, 48, 0], [255, 44, 0], [255, 40, 0], [255, 37, 0], [255, 33, 0],
    [255, 29, 0], [255, 26, 0], [255, 22, 0], [254, 18, 0], [250, 15, 0], [245, 11, 0], [241, 7, 0], [236, 3, 0],
    [232, 0, 0], [227, 0, 0], [222, 0, 0], [218, 0, 0], [213, 0, 0], [209, 0, 0], [204, 0, 0], [200, 0, 0],
    [195, 0, 0], [191, 0, 0], [186, 0, 0], [182, 0, 0], [177, 0, 0], [172, 0, 0], [168, 0, 0], [163, 0, 0],
    [159, 0, 0], [154, 0, 0], [150, 0, 0], [145, 0, 0], [141, 0, 0], [136, 0, 0], [132, 0, 0], [127, 0, 0]
], dtype=np.uint8)


def build_gradcam_models(model: Any) -> Tuple[Any, Any, str]:
    """Expose backbone activations and rebuild the frozen classification head."""
    import tensorflow as tf

    backbone = None
    for layer in getattr(model, "layers", []):
        if layer.name == "efficientnetb0" or isinstance(layer, tf.keras.Model):
            backbone = layer
            break

    if backbone is None:
        raise RuntimeError("EfficientNet-B0 backbone layer not found in model.")

    try:
        conv_layer = backbone.get_layer(GRADCAM_LAYER)
    except (ValueError, KeyError) as exc:
        raise RuntimeError(f"Target convolutional layer '{GRADCAM_LAYER}' not found.") from exc

    backbone_grad_model = tf.keras.Model(
        backbone.inputs, [conv_layer.output, backbone.output], name="efficientnet_gradcam_backbone"
    )

    backbone_index = model.layers.index(backbone)
    features = tf.keras.Input(shape=backbone.output.shape[1:], name="gradcam_features_input")
    output = features
    for layer in model.layers[backbone_index + 1:]:
        output = layer(output, training=False)
    classifier_head = tf.keras.Model(features, output, name="efficientnet_gradcam_head")

    return backbone_grad_model, classifier_head, GRADCAM_LAYER


def generate_gradcam_overlay(
    backbone_grad_model: Any,
    classifier_head: Any,
    tensor: Any,
) -> Tuple[float, str]:
    """Calculate exact Grad-CAM heatmap and return raw score and base64 PNG data URL."""
    import tensorflow as tf

    with tf.GradientTape() as tape:
        conv_output, features = backbone_grad_model(tensor, training=False)
        prediction = classifier_head(features, training=False)
        score = prediction[:, 0]

    raw_probability = float(prediction.numpy().reshape(-1)[0])

    gradients = tape.gradient(score, conv_output)
    if gradients is None:
        raise RuntimeError("Gradients are unavailable for the target layer.")

    weights = tf.reduce_mean(gradients, axis=(0, 1, 2))
    heatmap = tf.reduce_sum(conv_output[0] * weights, axis=-1)
    heatmap = tf.maximum(heatmap, 0)
    max_val = float(tf.reduce_max(heatmap).numpy())
    if max_val > 0:
        heatmap = heatmap / max_val

    heatmap_224 = tf.image.resize(heatmap[..., None], (224, 224)).numpy()[..., 0]
    if not np.isfinite(heatmap_224).all():
        raise RuntimeError("Grad-CAM heatmap contains non-finite values.")

    heatmap_clipped = np.clip(heatmap_224, 0.0, 1.0)

    # Colorize using precomputed JET_LUT without matplotlib
    indices = np.clip(np.round(heatmap_clipped * 255), 0, 255).astype(np.int32)
    colored = JET_LUT[indices]

    original = np.asarray(np.clip(tensor[0].numpy(), 0, 255), dtype=np.uint8)
    overlay = np.asarray(0.58 * original + 0.42 * colored, dtype=np.uint8)

    buffer = io.BytesIO()
    Image.fromarray(overlay).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    data_url = f"data:image/png;base64,{encoded}"

    return raw_probability, data_url
