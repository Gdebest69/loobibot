import string
import random
from discord.app_commands import TranslationContextLocation
from main import *


def id_generator(size=6, chars=string.ascii_lowercase):
    return "".join(random.choice(chars) for _ in range(size))


class MyCustomTranslator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ):
        """
        `locale_str` is the string that is requesting to be translated
        `locale` is the target language to translate to
        `context` is the origin of this string, eg TranslationContext.command_name, etc
        This function must return a string (that's been translated), or `None` to signal no available translation available, and will default to the original.
        """
        message_str = string.message
        context_location: TranslationContextLocation = context.location
        return message_str


async def setup(bot: LoobiBot):
    await bot.tree.set_translator(MyCustomTranslator())
