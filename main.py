import obspython as S
import pathlib
import re
import requests
import subprocess
import time

start_break_trigger_phrases = ["is it jump time", "break break break", "brake brake brake"]
stop_break_trigger_phrases = ["I'm back"]
close_game_phrases = ["close the game", "stop the game", "kill the game"]
privacy_mode_phrases = ["engage privacy mode", "activate privacy", "Chat please look away for a second"]

# This is the file where OBS writes the captions that go out to the world. It
# only works when the mic is unmuted.
path_to_live_captions_file = "/Users/adam/tmp/stream-captions.txt"

# This is the file that the shadow mic writes to. It works even when the mic is
# muted. As a result, the mic is always supposed to be muted.
#
# Keep in mind that the shadow mic is only added to certain scenes.
path_to_shadow_captions_file = "/Users/adam/tmp/stream-captions2.txt"

# This is what we'll mute when the trigger phrase is uttered
mic_name = "Mic/Aux"

shadow_mic_name = "Test duplicate mic"

regular_stream_scene_name = "Regular streaming"
game_scene_name = "Stream game"
privacy_scene_name = "Privacy"

# This is for vocalizing commands to run on my bot
bot_server_url = 'http://minipc:3001/run-fuzzy-command'
path_to_password_file = "/Volumes/inland/code/VocalStreamer/password.txt"

# Handle to the game process
game_proc = None

def set_scene_by_name(scene_name):
  scenes = S.obs_frontend_get_scenes()
  success = False
  for scene in scenes:
      name = S.obs_source_get_name(scene)
      if name == scene_name:
          S.obs_frontend_set_current_scene(scene)
          success = True
  S.source_list_release(scenes)
  if success:
    print("Successfully set the scene to " + scene_name)
  else:
    print("Could not find a scene with this name: " + scene_name)

def truncate_file(path):
  if pathlib.Path(path).exists():
    with open(path, "w") as file:
      file.truncate()

def collapse_file_text_to_string(text):
  return re.sub(r'[\n,.!?]', '', text).lower()

def was_trigger_phrase_uttered(phrases, path_to_captions_file):
  found_a_match = False
  with open(path_to_captions_file, "r", encoding="utf-8") as file:
    text = collapse_file_text_to_string(file.read())
    for trigger_phrase in phrases:
      if trigger_phrase in text:
        print("Trigger phrase found: " + trigger_phrase)
        found_a_match = True
        break

  if found_a_match:
    # Truncate the file so that we don't find the phrase again
    truncate_file(path_to_captions_file)

  return found_a_match

def check_for_commands():
  with open(path_to_live_captions_file, "r", encoding="utf-8") as file:
    text = collapse_file_text_to_string(file.read())
    match = re.match(r'.*check out the ([\w\s]+) command.*', text)
    if match is None:
      return

  truncate_file(path_to_live_captions_file)

  command = match.group(1)

  # It's possible that the command we got is very long depending on the trigger
  # phrase. For example, if the phrase is "check out the ____ command", then I
  # may say "check out the" first with no intention of talking about a command,
  # then say the final word minutes later and have a bunch of garbage in the
  # text.
  if len(command) > 75:
    print("Command is too long, not sending it to the server: " + command[:75])
    return

  print("Found a command match: " + command)

  password = read_password_from_file()
  myobj = {'password': password, 'query': command}
  response = requests.post(bot_server_url, json = myobj)

  print("Response from the bot: " + response.text)

def check_for_trigger_phrases():
  global game_proc

  check_for_commands()

  if was_trigger_phrase_uttered(start_break_trigger_phrases, path_to_live_captions_file):
    trigger_phrase_uttered()

  if was_trigger_phrase_uttered(privacy_mode_phrases, path_to_live_captions_file):
    set_scene_by_name(privacy_scene_name)

  # Remember: this will only work on scenes that have the shadow mic
  if was_trigger_phrase_uttered(stop_break_trigger_phrases, path_to_shadow_captions_file):
    set_mic_muted(False)
    set_scene_by_name(regular_stream_scene_name)

  if game_proc is not None:

    if was_trigger_phrase_uttered(close_game_phrases, path_to_live_captions_file) or was_trigger_phrase_uttered(close_game_phrases, path_to_shadow_captions_file):
      game_proc.kill()
      game_proc = None

# Returns True if this succeeded
def set_mic_muted(muted):
  print(f'{"Muting" if muted else "Unmuting"} the mic')
  mic = S.obs_get_source_by_name(mic_name)
  if mic is None:
    print(f"Couldn't find the mic by \"{mic_name}\" to be able to mute/unmute it")
  else:
    S.obs_source_set_muted(mic, muted)
    S.obs_source_release(mic)

  return mic is not None

def trigger_phrase_uttered():
  global game_proc
  if not set_mic_muted(True):
    # If the mic can't be muted, don't do anything else, that way there's an
    # obvious indicator that it couldn't be muted.
    return

  print("Launching Jump Royale")
  game_proc = subprocess.Popen(['/Applications/Godot_mono.app/Contents/MacOS/Godot', '--path', '/Volumes/inland/code/JumpRoyale/JumpRoyale'])

  time.sleep(1.0)

  # If the process couldn't start...
  if game_proc.poll() is not None:
    print("Godot already died. Unmuting the mic.")
    set_mic_muted(False)
    return

  print("Switching OBS scenes to the game")
  set_scene_by_name(game_scene_name)

def script_unload():
  S.timer_remove(check_for_trigger_phrases)

def make_strings_lowercase(strings):
  for i in range(len(strings)):
    strings[i] = strings[i].lower()

def read_password_from_file():
  with open(path_to_password_file, "r", encoding="utf-8") as file:
    return file.read().strip()

def main():
  print("Script is running")
  read_password_from_file()

  make_strings_lowercase(start_break_trigger_phrases)
  make_strings_lowercase(stop_break_trigger_phrases)
  make_strings_lowercase(close_game_phrases)
  make_strings_lowercase(privacy_mode_phrases)

  # Make sure we don't have any dangling trigger phrases
  truncate_file(path_to_live_captions_file)
  truncate_file(path_to_shadow_captions_file)

  S.timer_add(check_for_trigger_phrases, 500)
  print(f"Timer started to check for start-break phrases {start_break_trigger_phrases} and stop-break phrases {stop_break_trigger_phrases}")


main()
