from torch.nn import Tanh, Dropout, Parameter, AdaptiveAvgPool2d, Softmax, InstanceNorm2d, Flatten, PReLU, ReLU, Sequential, Conv2d, MaxPool2d, Module, BatchNorm1d, BatchNorm2d, Linear, Upsample, Sigmoid, LeakyReLU, MultiheadAttention
from torch.nn.functional import interpolate, adaptive_avg_pool2d
from torchvision import models
import torch

class Encoder(Module):
    def __init__(self):
        super(Encoder, self).__init__()

        self.layers = Sequential(
            Conv2d(in_channels=3, out_channels=32, kernel_size=4, stride=2, padding=1),
            BatchNorm2d(32),
            ReLU(inplace=True),
            Conv2d(in_channels=32, out_channels=64, kernel_size=4, stride=2, padding=1),
            BatchNorm2d(64),
            ReLU(inplace=True),
            Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(128),
            ReLU(inplace=True),
            Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(256),
            ReLU(inplace=True),
            Conv2d(in_channels=256, out_channels=256, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(256),
            ReLU(inplace=True),
            Conv2d(in_channels=256, out_channels=1, kernel_size=1),
        )

    def forward(self, x):
        x = self.layers(x)
        upsampled_x = interpolate(x, size=(8, 8), mode='bilinear', align_corners=False)
        return upsampled_x

# NOTE: CORRECT ORDER
class Classifier(Module):
    def __init__(self):
        super(Classifier, self).__init__()

        self.layers = Sequential(
            Conv2d(in_channels=3, out_channels=32, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(32),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=2, stride=2),
            Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(64),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=2, stride=2),
            Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(128),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=2, stride=2),
            Flatten(),
            Linear(in_features=128*8*8, out_features=256),
            ReLU(inplace=True),
            Linear(in_features=256, out_features=128),
            ReLU(inplace=True),
            Linear(in_features=128, out_features=5),
            Softmax(dim=1),
        )

    def forward(self, x):
        x = self.layers(x)
        return x

# NOTE: WRONG ORDER
"""class Classifier(Module):
    def __init__(self):
        super(Classifier, self).__init__()

        self.layers = Sequential(
            Conv2d(in_channels=3, out_channels=32, kernel_size=3, stride=1, padding=1),
            MaxPool2d(kernel_size=2, stride=2),
            BatchNorm2d(32),
            Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=2, stride=2),
            BatchNorm2d(64),
            Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=2, stride=2),
            BatchNorm2d(128),
            Flatten(),
            Linear(in_features=128*8*8, out_features=256),
            ReLU(inplace=True),
            Linear(in_features=256, out_features=128),
            ReLU(inplace=True),
            Linear(in_features=128, out_features=5),
            Softmax(dim=1)
        )

    def forward(self, x):
        x = self.layers(x)
        return x"""

class SelfAttention(Module):
    def __init__(self, in_channels):
        super(SelfAttention, self).__init__()

        self.query = Conv2d(in_channels, in_channels // 8, kernel_size=1)
        self.key = Conv2d(in_channels, in_channels // 8, kernel_size=1)
        self.value = Conv2d(in_channels, in_channels, kernel_size=1)
        self.gamma = Parameter(torch.zeros(1))
        self.softmax = Softmax(dim=-1)

    def forward(self, x):
        batch_size, channels, height, width = x.size()
        query = self.query(x).view(batch_size, -1, height * width).permute(0, 2, 1)
        key = self.key(x).view(batch_size, -1, height * width)
        value = self.value(x).view(batch_size, -1, height * width)
        attention_scores = torch.bmm(query, key)
        attention_scores = self.softmax(attention_scores)
        attention_output = torch.bmm(value, attention_scores.permute(0, 2, 1))
        attention_output = attention_output.view(batch_size, channels, height, width)
        x = self.gamma * attention_output + x
        return x

class Generator(Module):
    def __init__(self):
        super(Generator, self).__init__()

        self.layers = Sequential(
            Conv2d(257, 256, kernel_size=3, stride=1, padding=1),
            InstanceNorm2d(256),
            ReLU(inplace=True),
            Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            InstanceNorm2d(256),
            ReLU(inplace=True),
            Conv2d(256, 128, kernel_size=3, stride=1, padding=1),
            InstanceNorm2d(128),
            ReLU(inplace=True),
            #SelfAttention(in_channels=128),
            #SelfAttention(in_channels=128),
            Conv2d(128, 3, kernel_size=3, stride=1, padding=1),
        )

    def forward(self, x):
        x = self.layers(x)
        upsampled_x = interpolate(x, size=(64, 64), mode='bilinear', align_corners=False)
        return upsampled_x

class GaussianNoise(Module):
    def forward(self, x):
        if self.training:
            noise = torch.randn_like(x) * 0.1  # Adjust the noise level as needed
            x = x + noise
        return x

class Discriminator(Module):
    def __init__(self):
        super(Discriminator, self).__init__()

        self.layers = Sequential(
            Conv2d(in_channels=6, out_channels=64, kernel_size=4, stride=2, padding=1),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=64, out_channels=128, kernel_size=4, stride=2, padding=1),
            BatchNorm2d(128),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=128, out_channels=256, kernel_size=4, stride=2, padding=1),
            BatchNorm2d(256),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=256, out_channels=512, kernel_size=4, stride=2, padding=1),
            BatchNorm2d(512),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=512, out_channels=256, kernel_size=3, stride=1, padding=1),
        )

    def forward(self, x):
        x = self.layers(x)
        return x

class VGG19(Module):
    def __init__(self, pretrained=True, require_grad=False):
        super(VGG19, self).__init__()
        vgg_features = models.vgg19(pretrained=pretrained).features
        selected_layers = [vgg_features[i] for i in [0, 5, 10, 19, 28]]
        self.layers = Sequential(*selected_layers)

        for parameter in self.parameters():
            parameter.requires_grad = require_grad

    def forward(self, x):
        x = self.layers(x)
        return x

# NOTE: PRE-TRAINED VGG19 CLASSIFIER (SELECTED LAYERS)
"""class VGG19(Module):
    def __init__(self, pretrained=True, require_grad=False, num_classes=5):
        super(VGG19, self).__init__()
        vgg_features = models.vgg19(pretrained=pretrained).features

        selected_layers = [vgg_features[i] for i in [0, 5, 10, 19, 28]]
        self.layers = Sequential(*selected_layers)
        self.avgpool = adaptive_avg_pool2d
        self.classifier = Sequential(
            Linear(512 * 7 * 7, 4096),
            ReLU(True),
            Linear(4096, 4096),
            ReLU(True),
            Linear(4096, num_classes)
        )

        if not require_grad:
            for parameter in self.parameters():
                parameter.requires_grad = True

    def forward(self, x):
        features = self.layers(x)
        pooled_features = self.avgpool(features, (7, 7))
        pooled_features = pooled_features.view(pooled_features.size(0), -1)
        output = self.classifier(pooled_features)
        return output"""
