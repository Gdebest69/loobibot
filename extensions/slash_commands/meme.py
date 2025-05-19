from PIL import Image, ImageDraw
from io import BytesIO
from asyncio import to_thread
from main import *


class ImageLayer:
    def __init__(self, image: Image.Image, position: tuple[int, int]):
        self.image = image
        self.position = position

    @staticmethod
    def from_file(file_path, position: tuple[int, int]):
        return ImageLayer(Image.open(file_path).convert("RGBA"), position)

    @staticmethod
    def from_bytes(
        image_bytes: bytes,
        position: tuple[int, int],
        circle: bool = False,
        remove_transparency: bool = False,
    ):
        image = Image.open(BytesIO(image_bytes)).convert("RGBA")
        if remove_transparency:
            image = ImageLayer._remove_transparency(image)
        if circle:
            image = ImageLayer._make_circle(image)
        return ImageLayer(image, position)

    @staticmethod
    def _make_circle(image: Image.Image) -> Image.Image:
        """Crops an image into a circular shape."""
        size = (min(image.size),) * 2
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)

        image = image.resize(size, Image.LANCZOS)
        circular_image = Image.new("RGBA", size, (0, 0, 0, 0))
        circular_image.paste(image, mask=mask)
        return circular_image

    @staticmethod
    def _remove_transparency(image: Image.Image) -> Image.Image:
        """Replaces all transparent pixels with solid white."""
        new_image = Image.new("RGBA", image.size, (255, 255, 255, 255))
        new_image.paste(image, mask=image)
        return new_image

    def append_layer(self, layer: "ImageLayer", new_size: tuple[int, int] = None):
        """Appends another ImageLayer onto this image at its position, resizing it to the given pixel dimensions."""
        if new_size:
            resized_image = layer.image.resize(new_size, Image.LANCZOS)
        else:
            resized_image = layer.image
        self.image.paste(resized_image, layer.position, mask=resized_image)

    def to_discord_file(self, filename: str = "image.png") -> discord.File:
        """Returns the image layer as a Discord file."""
        img_bytes = BytesIO()
        self.image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return discord.File(img_bytes, filename=filename)

    def copy(self) -> "ImageLayer":
        """Returns a deep copy of the ImageLayer."""
        return ImageLayer(self.image.copy(), self.position)


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class MemeCommand(
    commands.GroupCog,
    name="meme",
    description="Generate meme images with user's avatars",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.lowtaperfade_base = ImageLayer.from_file(
            in_folder(os.path.join("assets", "memes", "ninja_lowtaperfade.png")), (0, 0)
        )
        self.ninja_hair = ImageLayer.from_file(
            in_folder(os.path.join("assets", "memes", "ninja_hair.png")), (0, 0)
        )

    @app_commands.command(
        name="lowtaperfade",
        description="Gives a user a low taper fade",
    )
    @app_commands.describe(user="The user to give low taper fade")
    async def meme_lowtaperfade(
        self, interaction: discord.Interaction, user: discord.User = None
    ):
        if user is None:
            user = interaction.user

        await interaction.response.defer()
        avatar_bytes = await user.display_avatar.read()

        def generate_image():
            base = self.lowtaperfade_base.copy()
            base.append_layer(
                ImageLayer.from_bytes(
                    avatar_bytes, (47, 80), circle=True, remove_transparency=True
                ),
                (190, 190),
            )
            base.append_layer(self.ninja_hair)
            return base.to_discord_file(
                f"Imagine if {user.display_name} had a low taper fade.png"
            )

        await interaction.edit_original_response(
            attachments=[await to_thread(generate_image)]
        )


async def setup(bot: LoobiBot):
    await bot.add_cog(MemeCommand(bot))
