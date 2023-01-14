# Python types
from __future__ import annotations
import io
import os.path
import random
import sys
import datetime

# Web types
from .forms import GenerateForm, RomForm
from django.conf import settings as conf

# Add the randomizer to the system path here.  This code assumes that the
# randomizer has been added at the site base path.
sys.path.append(os.path.join(conf.BASE_DIR, 'jetsoftime', 'sourcefiles'))

# Randomizer types
import bossrandotypes as rotypes
import ctenums
import randoconfig
import randomizer
import randosettings as rset


game_mode_map = {
    "standard": rset.GameMode.STANDARD,
    "lost_worlds": rset.GameMode.LOST_WORLDS,
    "ice_age": rset.GameMode.ICE_AGE,
    "legacy_of_cyrus": rset.GameMode.LEGACY_OF_CYRUS,
    "vanilla_rando": rset.GameMode.VANILLA_RANDO
}

shop_price_map = {
    "normal": rset.ShopPrices.NORMAL,
    "free": rset.ShopPrices.FREE,
    "mostly_random": rset.ShopPrices.MOSTLY_RANDOM,
    "fully_random": rset.ShopPrices.FULLY_RANDOM
}

difficulty_map = {
    "easy": rset.Difficulty.EASY,
    "normal": rset.Difficulty.NORMAL,
    "hard": rset.Difficulty.HARD
}

tech_order_map = {
    "normal": rset.TechOrder.NORMAL,
    "fully_random": rset.TechOrder.FULL_RANDOM,
    "balanced_random": rset.TechOrder.BALANCED_RANDOM
}


class InvalidSettingsException(Exception):
    pass


class RandomizerInterface:
    """
    RandomizerInterface acts as an interface between the web application
    and the Jets of Time randomizer code.

    All calls to the randomizer or its data are handled through this class.  It contains
    the appropriate methods for creating randomizer settings/config objects and querying
    them for information needed on the web generator.
    """
    def __init__(self, rom_data: bytearray):
        """
        Constructor for the RandomizerInterface class.

        :param rom_data: bytearray containing vanilla ROM data used to construct a randomizer object
        """
        self.randomizer = randomizer.Randomizer(rom_data, is_vanilla=True)

    def configure_seed_from_form(self, form: GenerateForm) -> str:
        """
        Generate a RandoConfig from the provided GenerateForm.
        This will convert the form data into the appropriate randomizer settings and config
        objects and then tell the randomizer to generate a seed.

        :param form: GenerateForm with the user's settings

        :return: string of a nonce, if any, that was used to obfuscate the seed
        """
        self.randomizer.settings = self.__convert_form_to_settings(form)
        nonce = ''
        # If this is a race seed, modify the seed value  before sending it through
        # the randomizer.  This will ensure that race ROMs and non-race ROMs with the same
        # seed value are not identical.
        if form.cleaned_data['spoiler_log']:
            self.randomizer.set_random_config()
        else:
            # Use the current timestamp's number of microseconds as an arbitrary nonce value
            nonce = str(datetime.datetime.now().microsecond)
            seed = self.randomizer.settings.seed
            self.randomizer.settings.seed = seed + nonce
            self.randomizer.set_random_config()
            self.randomizer.settings.seed = seed
        return nonce

    def configure_seed_from_settings(self, settings: rset.Settings, is_race_seed: bool) -> str:
        """
        Generate a RandoConfig from the provided Settings object.
        This will create a new game based on existing settings.

        This method will fail if the given settings object is for a mystery seed.

        :param settings: Settings object to copy for this new game
        :param is_race_seed: Whether or not this is a race seed

        :return: string of a nonce, if any, that was used to obfuscate the seed
        """

        if rset.GameFlags.MYSTERY in settings.gameflags:
            raise InvalidSettingsException("Mystery seeds cannot be cloned.")

        self.randomizer.settings = settings
        # get a random seed value to replace the existing one
        seed = settings.seed
        new_seed = seed
        while seed == new_seed:
            new_seed = self.get_random_seed()
        settings.seed = new_seed
        nonce = ''

        # If this is a race seed, modify the seed value  before sending it through
        # the randomizer.  This will ensure that race ROMs and non-race ROMs with the same
        # seed value are not identical.
        if is_race_seed:
            nonce = str(datetime.datetime.now().microsecond)
            self.randomizer.settings.seed = new_seed + nonce
            self.randomizer.set_random_config()
            self.randomizer.settings.seed = new_seed
        else:
            self.randomizer.set_random_config()
        return nonce

    def generate_rom(self) -> bytearray:
        """
        Create a ROM from the settings and config objects previously generated or set.

        :return: bytearray object with the modified ROM data
        """
        self.randomizer.generate_rom()
        return self.randomizer.get_generated_rom()

    def set_settings_and_config(self, settings: rset.Settings, config: randoconfig.RandoConfig, form: RomForm):
        """
        Populate the randomizer with a pre-populated RandoSettings object and a
        preconfigured RandoSettings object.

        :param settings: RandoSettings object
        :param config: RandoConfig object
        :param form: RomForm with cosmetic settings
        """
        # Cosmetic settings
        if form.cleaned_data['reduce_flashes']:
            settings.cosmetic_flags = settings.cosmetic_flags | rset.CosmeticFlags.REDUCE_FLASH

        if form.cleaned_data['zenan_alt_battle_music']:
            settings.cosmetic_flags = settings.cosmetic_flags | rset.CosmeticFlags.ZENAN_ALT_MUSIC

        if form.cleaned_data['death_peak_alt_music']:
            settings.cosmetic_flags = settings.cosmetic_flags | rset.CosmeticFlags.DEATH_PEAK_ALT_MUSIC

        if form.cleaned_data['quiet_mode']:
            settings.cosmetic_flags = settings.cosmetic_flags | rset.CosmeticFlags.QUIET_MODE

        # Character/Epoch renames
        settings.char_names[0] = self.get_character_name(form.cleaned_data['crono_name'], 'Crono')
        settings.char_names[1] = self.get_character_name(form.cleaned_data['marle_name'], 'Marle')
        settings.char_names[2] = self.get_character_name(form.cleaned_data['lucca_name'], 'Lucca')
        settings.char_names[3] = self.get_character_name(form.cleaned_data['robo_name'], 'Robo')
        settings.char_names[4] = self.get_character_name(form.cleaned_data['frog_name'], 'Frog')
        settings.char_names[5] = self.get_character_name(form.cleaned_data['ayla_name'], 'Ayla')
        settings.char_names[6] = self.get_character_name(form.cleaned_data['magus_name'], 'Magus')
        settings.char_names[7] = self.get_character_name(form.cleaned_data['epoch_name'], 'Epoch')

        # In-game options
        # Boolean options
        if form.cleaned_data['stereo_audio'] is not None:
            settings.ctoptions.stereo_audio = form.cleaned_data['stereo_audio']

        if form.cleaned_data['save_menu_cursor'] is not None:
            settings.ctoptions.save_menu_cursor = form.cleaned_data['save_menu_cursor']

        if form.cleaned_data['save_battle_cursor'] is not None:
            settings.ctoptions.save_battle_cursor = form.cleaned_data['save_battle_cursor']

        if form.cleaned_data['skill_item_info'] is not None:
            settings.ctoptions.skill_item_info = form.cleaned_data['skill_item_info']

        if form.cleaned_data['consistent_paging'] is not None:
            settings.ctoptions.consistent_paging = form.cleaned_data['consistent_paging']

        # Integer options
        if form.cleaned_data['battle_speed']:
            settings.ctoptions.battle_speed = \
                self.clamp((form.cleaned_data['battle_speed'] - 1), 0, 7)

        if form.cleaned_data['background_selection']:
            settings.ctoptions.menu_background = \
                self.clamp((form.cleaned_data['background_selection'] - 1), 0, 7)

        if form.cleaned_data['battle_message_speed']:
            settings.ctoptions.battle_msg_speed = \
                self.clamp((form.cleaned_data['battle_message_speed'] - 1), 0, 7)

        if form.cleaned_data['battle_gauge_style'] is not None:
            settings.ctoptions.battle_gauge_style = \
                self.clamp((form.cleaned_data['battle_gauge_style']), 0, 2)

        self.randomizer.settings = settings
        self.randomizer.config = config

    def get_settings(self) -> rset.Settings:
        """
        Get the settings object used to generate the seed.

        :return: RandoSettings object used to generate the seed
        """
        return self.randomizer.settings

    def get_config(self) -> randoconfig.RandoConfig:
        """
        Get the config object used to generate the the seed.

        :return: RandoConfig object used to generate the seed
        """
        return self.randomizer.config

    def get_rom_name(self, share_id: str) -> str:
        """
        Get the ROM name for this seed

        :param share_id: Share ID os the seed in question
        :return: String containing the name of the ROM for this seed
        """
        if rset.GameFlags.MYSTERY in self.randomizer.settings.gameflags:
            return "ctjot_mystery_" + share_id + ".sfc"
        else:
            return "ctjot_" + self.randomizer.settings.get_flag_string() + "_" + share_id + ".sfc"

    @classmethod
    def __convert_form_to_settings(cls, form: GenerateForm) -> rset.Settings:
        """
        Convert flag/settings data from the web form into a RandoSettings object.

        :param form: GenerateForm object from the web interface
        :return: RandoSettings object with flags/settings from the form applied
        """

        settings = rset.Settings()

        # Seed
        if form.cleaned_data['seed'] == "":
            # get a random seed
            settings.seed = cls.get_random_seed()
        else:
            settings.seed = form.cleaned_data['seed']

        settings.item_difficulty = rset.Difficulty.NORMAL
        settings.enemy_difficulty = rset.Difficulty.NORMAL
        settings.game_mode = rset.GameMode.LEGACY_OF_CYRUS
        settings.techorder = rset.TechOrder.FULL_RANDOM

        # flags
        settings.gameflags = settings.gameflags | rset.GameFlags.FIX_GLITCH
        settings.gameflags = settings.gameflags | rset.GameFlags.FAST_PENDANT
        settings.gameflags = settings.gameflags | rset.GameFlags.UNLOCKED_MAGIC
        settings.gameflags = settings.gameflags | rset.GameFlags.GEAR_RANDO
        settings.gameflags = settings.gameflags | rset.GameFlags.FAST_TABS

        return settings
    # End __convert_form_to_settings

    @classmethod
    def get_spoiler_log(cls, config: randoconfig.RandoConfig, settings: rset.Settings) -> io.StringIO:
        """
        Get a spoiler log file-like object.

        :param config: RandoConfig object describing the seed
        :param settings: RandoSettings object describing the seed
        :return: File-like object with spoiler log data for the given seed data
        """
        spoiler_log = io.StringIO()
        rando = randomizer.Randomizer(cls.get_base_rom(), is_vanilla=True, settings=settings, config=config)

        # The Randomizer.write_spoiler_log method writes directly to a file,
        # but it works if we pass a StringIO instead.
        rando.write_spoiler_log(spoiler_log)

        return spoiler_log

    @classmethod
    def get_json_spoiler_log(cls, config: randoconfig.RandoConfig, settings: rset.Settings) -> io.StringIO:
        """
        Get a spoiler log file-like object.

        :param config: RandoConfig object describing the seed
        :param settings: RandoSettings object describing the seed
        :return: File-like object with spoiler log data for the given seed data
        """
        spoiler_log = io.StringIO()
        rando = randomizer.Randomizer(cls.get_base_rom(), is_vanilla=True, settings=settings, config=config)

        # The Randomizer.write_spoiler_log method writes directly to a file,
        # but it works if we pass a StringIO instead.
        rando.write_json_spoiler_log(spoiler_log)

        return spoiler_log

    @staticmethod
    def get_web_spoiler_log(config: randoconfig.RandoConfig) -> dict[str, list[dict[str, str]]]:
        """
        Get a dictionary representing the spoiler log data for the given seed.

        :param config: RandoConfig object describing the seed
        :return: Dictionary of spoiler data
        """
        spoiler_log = {
            'characters': [],
            'key_items': [],
            'bosses': []
        }

        # Character data
        for recruit_spot in config.char_assign_dict.keys():
            held_char = config.char_assign_dict[recruit_spot].held_char
            reassign_char = \
                config.pcstats.get_character_assignment(held_char)
            char_data = {'location': str(f"{recruit_spot}"),
                         'character': str(f"{held_char}"),
                         'reassign': str(f"{reassign_char}")}
            spoiler_log['characters'].append(char_data)

        # Key item data
        for location in config.key_item_locations:
            spoiler_log['key_items'].append(
                {'location': str(f"{location.getName()}"), 'key': str(location.getKeyItem())})

        # Boss data
        for location in config.boss_assign_dict.keys():
            if config.boss_assign_dict[location] == rotypes.BossID.TWIN_BOSS:
                twin_type = config.boss_data_dict[rotypes.BossID.TWIN_BOSS].parts[0].enemy_id
                twin_name = config.enemy_dict[twin_type].name
                boss_str = "Twin " + str(twin_name)
            else:
                boss_str = str(config.boss_assign_dict[location])
            spoiler_log['bosses'].append({'location': str(location), 'boss': boss_str})

        return spoiler_log
    # End get_web_spoiler_log

    @staticmethod
    def get_random_seed() -> str:
        """
        Get a random seed string for a ROM.
        This seed string is built up from a list of names bundled with the randomizer.  This method
        expects the names.txt file to be accessible in the web app's root directory.

        :return: Random seed string.
        """
        with open("names.txt", "r") as names_file:
            names = names_file.readline()
            names = names.split(",")
        return "".join(random.choice(names) for i in range(2))

    @staticmethod
    def get_base_rom() -> bytearray:
        """
        Read in the server's vanilla ROM as a bytearray.
        This data is used to create a RandoConfig object to generate a seed.  It should not
        be used when applying the config and sending the seed to a user.  The user's ROM will
        be used for that process instead.

        The unheadered, vanilla Chrono Trigger ROM must be located in the web app's BASE_DIR
        and must be named ct.sfc.

        :return: bytearray containing the vanilla Chrono Trigger ROM data
        """
        with open(str("ct.sfc"), 'rb') as infile:
            rom = bytearray(infile.read())
        return rom

    @classmethod
    def get_share_details(cls, config: randoconfig.RandoConfig, settings: rset.Settings) -> io.StringIO:
        """
        Get details about a seed for display on the seed share page.  If this is a mystery seed then
        just display "Mystery seed!".


        :param config: RandoConfig object describing this seed
        :param settings: RandoSettings object describing this seed
        :return: File-like object with seed share details
        """
        buffer = io.StringIO()
        rando = randomizer.Randomizer(cls.get_base_rom(), is_vanilla=True, settings=settings, config=config)

        if rset.GameFlags.MYSTERY in settings.gameflags:
            # TODO - Get weights and non-mystery flags
            # NOTE - The randomizer overwrites the settings object when it is a mystery seed and wipes
            #        out the seed value and most of the probability data.  Either the "before" version
            #        of this object will need to be stored or the randomizer will need to be modified
            #        to preserve this information if we want more information here.
            buffer.write("Mystery seed!\n")
        else:
            # For now just use the settings spoiler output for the share link display.
            # TODO - Make this more comprehensive.
            buffer.write("Seed: " + settings.seed + "\n")
            rando.write_settings_spoilers(buffer)

        return buffer

    @staticmethod
    def get_character_name(name: str, default_name: str):
        """
        Given a character name and a default, validate the name and return either the
        validated name or the default value if the name is invalid.

        Valid names are five characters or less, alphanumeric characters only.

        :param name: Name selected by the user
        :param default_name: Default name of the character
        :return: Either the user's selected name or a default if the name is invalid.
        """
        if name is None or name == "" or len(name) > 5 or not name.isalnum():
            return default_name
        return name

    @staticmethod
    def clamp(value, min_val, max_val):
        return max(min_val, min(value, max_val))

