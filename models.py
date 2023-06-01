from torch.nn import ReLU, Sequential, Conv2d, MaxPool2d, Module, BatchNorm2d, ConvTranspose2d, InstanceNorm2d, Tanh, LeakyReLU, MultiheadAttention
from torch.nn.functional import interpolate

class SelfAttention(Module):
    def __init__(self, in_channels, num_heads):
        super(SelfAttention, self).__init__()
        self.multihead_attention = MultiheadAttention(embed_dim=in_channels, num_heads=num_heads)
    
    def forward(self, x):
        batch_size, in_channels, width, length = x.size()
        x = x.permute(2, 3, 0, 1).reshape(width * length, batch_size, in_channels)
        output, _ = self.multihead_attention(x, x, x)  # (x, x, x) = (query, key, value)
        output = output.reshape(width, length, batch_size, in_channels).permute(2, 3, 0, 1)
        return output

class Encoder(Module):
    def __init__(self):
        super(Encoder, self).__init__()

        self.layers = Sequential(
            Conv2d(in_channels=1, out_channels=32, kernel_size=3, stride=1, padding=1),
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
            Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(256),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=2, stride=2),
            Conv2d(in_channels=256, out_channels=256, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(256),
            ReLU(inplace=True),
            Conv2d(in_channels=256, out_channels=1, kernel_size=1),
        )

    def forward(self, x):
        x = self.layers(x)
        upsampled_x = interpolate(x, size=(8, 8), mode='bilinear', align_corners=False)
        return upsampled_x

class Generator(Module):
    def __init__(self):
        super(Generator, self).__init__()

        self.layers = Sequential(
            ConvTranspose2d(in_channels=257, out_channels=256, kernel_size=4, stride=2, padding=1),
            InstanceNorm2d(256),
            ReLU(inplace=True),
            ConvTranspose2d(in_channels=256, out_channels=128, kernel_size=4, stride=2, padding=1),
            InstanceNorm2d(128),
            ReLU(inplace=True),
            SelfAttention(in_channels=128, num_heads=4),
            SelfAttention(in_channels=128, num_heads=4),
            ConvTranspose2d(in_channels=128, out_channels=3, kernel_size=4, stride=2, padding=1),
            Tanh(),
        )

    def forward(self, x):
        x = self.layers(x)
        return x

class Discriminator(Module):
    def __init__(self):
        super(Discriminator, self).__init__()

        self.layers = Sequential(
            Conv2d(in_channels=3, out_channels=64, kernel_size=4, stride=2, padding=1),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=64, out_channels=128, kernel_size=4, stride=2, padding=1),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=128, out_channels=256, kernel_size=4, stride=2, padding=1),
            LeakyReLU(0.2, inplace=True),
            Conv2d(in_channels=256, out_channels=256, kernel_size=4, stride=2, padding=1),
            LeakyReLU(0.2, inplace=True),
        )

    def forward(self, x):
        x = self.layers(x)
        return x