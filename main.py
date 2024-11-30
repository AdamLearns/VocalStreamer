import obspython as S
import pathlib
import re
import requests
import subprocess
import time
import threading

start_jump_royale_trigger_phrases = ["is it jump time", "is a jump time", "break break break", "brake brake brake"]
start_animal_royale_trigger_phrases = ["is it tnt time", "is it tnd time", "is it t&d time"]
stop_break_trigger_phrases = ["I'm back"]
close_game_phrases = ["close the game", "close the the game", "closed the game", "closed game", "stop the game", "kill the game"]
privacy_mode_phrases = ["engage privacy", "engage privacy mode", "activate privacy", "Chat please look away for a second"]

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

just_monitor_scene_name = "Just monitor"
regular_stream_scene_name = "Regular streaming"
game_scene_name = "Stream game"
privacy_scene_name = "Privacy"

# This is for vocalizing commands to run on my bot
bot_server_url = 'http://minipc:3001/run-fuzzy-command'
path_to_password_file = "/Volumes/inland/code/VocalStreamer/password.txt"

# Handle to the game process
jump_royale_proc = None
minecraft_prism_proc = None
minecraft_server_proc = None

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
  global jump_royale_proc
  global minecraft_server_proc
  global minecraft_prism_proc

  check_for_commands()

  if was_trigger_phrase_uttered(start_jump_royale_trigger_phrases, path_to_live_captions_file):
    start_jump_royale()

  if was_trigger_phrase_uttered(start_animal_royale_trigger_phrases, path_to_live_captions_file):
    thread = threading.Thread(target=start_animal_royale)
    thread.start()

  if was_trigger_phrase_uttered(privacy_mode_phrases, path_to_live_captions_file):
    set_scene_by_name(privacy_scene_name)

  # Remember: this will only work on scenes that have the shadow mic
  if was_trigger_phrase_uttered(stop_break_trigger_phrases, path_to_shadow_captions_file):
    set_mic_muted(False)
    set_scene_by_name(regular_stream_scene_name)

  if jump_royale_proc is not None:

    if was_trigger_phrase_uttered(close_game_phrases, path_to_live_captions_file) or was_trigger_phrase_uttered(close_game_phrases, path_to_shadow_captions_file):
      print("Killing Jump Royale")
      jump_royale_proc.kill()
      jump_royale_proc = None

  if minecraft_server_proc is not None:

    if was_trigger_phrase_uttered(close_game_phrases, path_to_live_captions_file) or was_trigger_phrase_uttered(close_game_phrases, path_to_shadow_captions_file):
      print("Killing Animal Royale")
      minecraft_server_proc.kill()
      minecraft_server_proc = None

      if minecraft_prism_proc is not None:
        minecraft_prism_proc.kill()
        minecraft_prism_proc = None

      kill_minecraft_client()

def kill_minecraft_client():
  subprocess.Popen("kill $(ps aux | grep 'PrismLauncher/libraries/com/mojang/minecraft' | grep -v grep | awk '{print $2}')", shell=True)

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

def start_animal_royale():
  global minecraft_prism_proc
  global minecraft_server_proc
  if not set_mic_muted(True):
    # If the mic can't be muted, don't do anything else, that way there's an
    # obvious indicator that it couldn't be muted.
    return

  set_scene_by_name(just_monitor_scene_name)

  # To debug, add "-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005" to the string
  cmd_string = "java -Xms8192M -Xmx8192M -XX:+AlwaysPreTouch -XX:+DisableExplicitGC -XX:+ParallelRefProcEnabled -XX:+PerfDisableSharedMem -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1HeapRegionSize=8M -XX:G1HeapWastePercent=5 -XX:G1MaxNewSizePercent=40 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1NewSizePercent=30 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:G1ReservePercent=20 -XX:InitiatingHeapOccupancyPercent=15 -XX:MaxGCPauseMillis=200 -XX:MaxTenuringThreshold=1 -XX:SurvivorRatio=32 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true -jar paper-1.21.3-66.jar nogui"
  server_arg_array = cmd_string.split()

  print("Starting the Minecraft server")
  minecraft_server_proc = subprocess.Popen(server_arg_array, cwd="/Users/adam/Downloads/paper")

  num_attempts = 0
  while True:
    if minecraft_server_proc.poll() is not None:
      minecraft_server_proc = None
      print("Minecraft server died.")
      return

    # We could do "curl localhost:25565" or use the Python module mcstatus,
    # but this is pretty easy, too
    lsof_proc = subprocess.Popen(['lsof', '-nP', '-iTCP', '-sTCP:LISTEN'], stdout=subprocess.PIPE)

    try:
      lsof_proc.wait(3)
    except TimeoutExpired:
      lsof_proc.kill()
      minecraft_server_proc.kill()
      minecraft_server_proc = None
      print("lsof timed out")
      return

    server_is_ready = "25565" in str(lsof_proc.stdout.read())
    if server_is_ready:
      break

    num_attempts += 1
    if num_attempts > 30:
      print("Minecraft server didn't start up after 30 attempts.")
      minecraft_server_proc.kill()
      minecraft_server_proc = None
      return

    time.sleep(0.5)

  # We now know that the Minecraft server is running and can accept connections
  print("Minecraft server is ready. Starting the client.")
  minecraft_prism_proc = subprocess.Popen(['/Applications/Prism Launcher.app/Contents/MacOS/prismlauncher', '--launch', '1.21.3'])

  # We just trust that this worked. If we want to verify it through code, we
  # would need something like https://github.com/py-mine/mcstatus

def start_jump_royale():
  global jump_royale_proc
  if not set_mic_muted(True):
    # If the mic can't be muted, don't do anything else, that way there's an
    # obvious indicator that it couldn't be muted.
    return

  print("Launching Jump Royale")
  jump_royale_proc = subprocess.Popen(['/Applications/Godot_mono.app/Contents/MacOS/Godot', '--path', '/Volumes/inland/code/JumpRoyale/JumpRoyale'])

  time.sleep(1.0)

  # If the process couldn't start...
  if jump_royale_proc.poll() is not None:
    jump_royale_proc = None
    print("Godot already died.")
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

  make_strings_lowercase(start_jump_royale_trigger_phrases)
  make_strings_lowercase(stop_break_trigger_phrases)
  make_strings_lowercase(close_game_phrases)
  make_strings_lowercase(privacy_mode_phrases)

  # Make sure we don't have any dangling trigger phrases
  truncate_file(path_to_live_captions_file)
  truncate_file(path_to_shadow_captions_file)

  S.timer_add(check_for_trigger_phrases, 500)
  print(f"Timer started to check for start-break phrases {start_jump_royale_trigger_phrases} and stop-break phrases {stop_break_trigger_phrases}")


main()
