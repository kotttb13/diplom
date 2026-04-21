"""
Создание реальных тестовых моделей/данных для оптимизации и квантования.
Данные не моковые: используется CIFAR-10.
"""

import os
import shutil
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import tensorflow as tf

BASE_DIR = os.path.join("app", "data", "test_models")
TORCH_DIR = os.path.join(BASE_DIR, "pytorch_cifar10")
TF_DIR = os.path.join(BASE_DIR, "tensorflow_cifar10")
ONNX_DIR = os.path.join(BASE_DIR, "onnx_cifar10")
RAW_DIR = os.path.join(BASE_DIR, "cifar10_data")
TEMP_DATA_ROOT = os.path.join(BASE_DIR, "_temp_cifar10")

for path in [BASE_DIR, TORCH_DIR, TF_DIR, ONNX_DIR, RAW_DIR]:
    os.makedirs(path, exist_ok=True)

print("=== Создание реальных тестовых моделей на CIFAR-10 ===")

# Общие данные CIFAR-10
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
y_train = y_train.reshape(-1)
y_test = y_test.reshape(-1)
x_train = x_train.astype(np.float32) / 255.0
x_test = x_test.astype(np.float32) / 255.0
np.save(os.path.join(RAW_DIR, "test_images.npy"), x_test)
np.save(os.path.join(RAW_DIR, "test_labels.npy"), y_test)
print(f"[OK] CIFAR-10 сохранен: {x_test.shape}, labels={y_test.shape}")


def create_tf_model():
    return tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(32, 32, 3)),
            tf.keras.layers.Conv2D(32, 3, padding="same", activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, padding="same", activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dense(10, activation="softmax"),
        ]
    )


# TensorFlow артефакты
print("[1/3] TensorFlow: обучение и экспорт")
tf_model = create_tf_model()
tf_model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
# Короткое обучение на реальных данных (без моков)
tf_model.fit(x_train[:12000], y_train[:12000], epochs=2, batch_size=64, verbose=1)
loss, acc = tf_model.evaluate(x_test, y_test, verbose=0)
print(f"TF accuracy: {acc:.4f}")
tf_model.save(os.path.join(TF_DIR, "cifar10_cnn.h5"))
tf_model.save(os.path.join(TF_DIR, "cifar10_cnn.keras"))

converter = tf.lite.TFLiteConverter.from_keras_model(tf_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_bytes = converter.convert()
with open(os.path.join(TF_DIR, "cifar10_cnn.tflite"), "wb") as f:
    f.write(tflite_bytes)

np.save(os.path.join(TF_DIR, "test_data.npy"), x_test)
np.save(os.path.join(TF_DIR, "test_labels.npy"), y_test)
np.save(os.path.join(TF_DIR, "calibration_data.npy"), x_train[:256])


class SmallCifarCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 8 * 8, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


# PyTorch артефакты
print("[2/3] PyTorch: обучение и экспорт")
transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ]
)
train_set = datasets.CIFAR10(root=TEMP_DATA_ROOT, train=True, download=True, transform=transform)
test_set = datasets.CIFAR10(root=TEMP_DATA_ROOT, train=False, download=True, transform=transform)
train_loader = torch.utils.data.DataLoader(train_set, batch_size=128, shuffle=True)
test_loader = torch.utils.data.DataLoader(test_set, batch_size=256, shuffle=False)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_model = SmallCifarCNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(torch_model.parameters(), lr=1e-3)

torch_model.train()
for epoch in range(2):
    total_loss = 0.0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        logits = torch_model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item())
    print(f"Torch epoch {epoch + 1}: loss={total_loss / len(train_loader):.4f}")

torch_model.eval()
correct, total = 0, 0
with torch.no_grad():
    for xb, yb in test_loader:
        xb, yb = xb.to(device), yb.to(device)
        pred = torch_model(xb).argmax(dim=1)
        correct += int((pred == yb).sum().item())
        total += int(yb.size(0))
print(f"Torch accuracy: {correct / total:.4f}")

torch.save(torch_model.state_dict(), os.path.join(TORCH_DIR, "cifar10_cnn_state_dict.pth"))
torch.save(torch_model.cpu(), os.path.join(TORCH_DIR, "cifar10_cnn_full.pt"))
scripted = torch.jit.script(torch_model.cpu())
scripted.save(os.path.join(TORCH_DIR, "cifar10_cnn_scripted.pt"))

all_x, all_y = [], []
for xb, yb in test_loader:
    all_x.append(xb.numpy())
    all_y.append(yb.numpy())
x_test_nchw = np.concatenate(all_x, axis=0).astype(np.float32)
y_test_torch = np.concatenate(all_y, axis=0).astype(np.int64)

np.save(os.path.join(TORCH_DIR, "test_data.npy"), x_test_nchw)
np.save(os.path.join(TORCH_DIR, "test_labels.npy"), y_test_torch)
np.save(os.path.join(TORCH_DIR, "calibration_data.npy"), x_test_nchw[:256])


# ONNX артефакты
print("[3/3] ONNX: экспорт из PyTorch")
dummy = torch.randn(1, 3, 32, 32)
torch.onnx.export(
    torch_model.cpu(),
    dummy,
    os.path.join(ONNX_DIR, "cifar10_cnn.onnx"),
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
    opset_version=13,
)
np.save(os.path.join(ONNX_DIR, "test_data.npy"), x_test_nchw)
np.save(os.path.join(ONNX_DIR, "test_labels.npy"), y_test_torch)
np.save(os.path.join(ONNX_DIR, "calibration_data.npy"), x_test_nchw[:256])

readme = """# Реальные тестовые модели и данные (CIFAR-10)

Содержимое подготовлено для тестирования оптимизации и квантования.

## Важно для загрузки PyTorch в UI
- Используйте `pytorch_cifar10/cifar10_cnn_full.pt` или `pytorch_cifar10/cifar10_cnn_scripted.pt`.
- `cifar10_cnn_state_dict.pth` сохранен только как reference-артефакт, не как основной файл для автоконвертации.

## Данные для проверки качества и static quantization
- `test_data.npy` + `test_labels.npy` — для валидации.
- `calibration_data.npy` — для калибровки static-квантования.

## Форматы
- TensorFlow: NHWC `(N, 32, 32, 3)`
- PyTorch/ONNX: NCHW `(N, 3, 32, 32)`
"""
with open(os.path.join(BASE_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

shutil.rmtree(TEMP_DATA_ROOT, ignore_errors=True)
print("Готово. Артефакты сохранены в app/data/test_models")