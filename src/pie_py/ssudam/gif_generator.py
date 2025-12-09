from importlib import resources
from io import BytesIO
from typing import IO

from PIL import Image
from PIL.ImageFile import ImageFile
import fsspec

class GIFGenerator:
    WIDTH = 112
    HEIGHT = 112
    FRAMES = 5
    DURATION = 60

    scales: list[tuple[int, int, int, int]] = [
        (15, 20, 97, 97),
        (12, 33, 102, 84),
        (9, 40, 110, 78),
        (10, 33, 102, 85),
        (13, 20, 97, 100)
    ]

    def __init__(self):
        self.ssudam_frames: list[ImageFile] | None = None

    def load(self):
        path = resources.files(__package__) / 'ssudam.gif'
        raw_gif = Image.open(path)
        self.ssudam_frames = list()

        for i in range(GIFGenerator.FRAMES):
            raw_gif.seek(i)
            self.ssudam_frames.append(raw_gif.convert('RGBA'))

    def generate_gif(self, source_image: ImageFile) -> bytes:
        blank_image = Image.new("RGBA", (GIFGenerator.WIDTH, GIFGenerator.HEIGHT), (0, 0, 0, 0))
        frames = [blank_image.copy() for _ in range(GIFGenerator.FRAMES)]

        for i, frame in enumerate(frames):
            scale = GIFGenerator.scales[i]
            resized_image = source_image.resize(scale[2:4])
            frame.paste(resized_image, scale[0:2], resized_image)
            frame.paste(self.ssudam_frames[i], (0, 0), self.ssudam_frames[i])

        output = BytesIO()

        frames[0].save(
            output,
            save_all=True,
            append_images=frames[1:],
            duration=GIFGenerator.DURATION,
            disposal=2,
            loop=0,
            format='GIF'
        )

        return output.getvalue()