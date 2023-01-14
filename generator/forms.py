from django import forms


#
# This form is used to submit the ROM on the page where seeds are downloaded.
#
class RomForm(forms.Form):
    rom_file = forms.FileField(required=True)
    share_id = forms.CharField(widget=forms.HiddenInput(), required=True)

    # Cosmetic
    zenan_alt_battle_music = forms.BooleanField(required=False)
    death_peak_alt_music = forms.BooleanField(required=False)
    quiet_mode = forms.BooleanField(required=False)
    reduce_flashes = forms.BooleanField(required=False)

    # Actual character name length is limited to 5 characters in game,
    # but if an invalid name is entered the randomizer interface will
    # just use the character's default name.
    crono_name = forms.CharField(max_length=15, required=False)
    marle_name = forms.CharField(max_length=15, required=False)
    lucca_name = forms.CharField(max_length=15, required=False)
    robo_name = forms.CharField(max_length=15, required=False)
    frog_name = forms.CharField(max_length=15, required=False)
    ayla_name = forms.CharField(max_length=15, required=False)
    magus_name = forms.CharField(max_length=15, required=False)
    epoch_name = forms.CharField(max_length=15, required=False)

    # In-game options
    stereo_audio = forms.BooleanField(required=False)
    save_menu_cursor = forms.BooleanField(required=False)
    save_battle_cursor = forms.BooleanField(required=False)
    save_skill_item_cursor = forms.BooleanField(required=False)
    skill_item_info = forms.BooleanField(required=False)
    consistent_paging = forms.BooleanField(required=False)
    background_selection = forms.IntegerField(required=False)
    battle_speed = forms.IntegerField(required=False)
    battle_message_speed = forms.IntegerField(required=False)
    battle_gauge_style = forms.IntegerField(required=False)


#
# Form class for version 3.2.0 of the randomizer.
#
class GenerateForm(forms.Form):
    # seed and spoiler log
    seed = forms.CharField(max_length=25, required=False)
    spoiler_log = forms.BooleanField(required=False)
