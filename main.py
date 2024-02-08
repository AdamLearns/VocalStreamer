import obspython as S
import pathlib
import subprocess

trigger_phrases = ["is it jump time", "break break break", "brake brake brake"]
path_to_captions_file = "/Users/adam/tmp/stream-captions.txt"

# This is what we'll mute when the trigger phrase is uttered
mic_name = "Mic/Aux"

# This is the scene we'll switch to when the trigger phrase is uttered
scene_name_to_switch_to = "Stream game"

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

def was_trigger_phrase_uttered():
  with open(path_to_captions_file, "r") as file:
    for line in file:
      line = line.replace(",", "").replace(".", "")
      for trigger_phrase in trigger_phrases:
        if trigger_phrase in line:
          print("Trigger phrase found: " + trigger_phrase)
          # Delete the file so that we don't find the phrase again
          truncate_file(path_to_captions_file)
          return True

  return False

def check_for_trigger_phrase():
  if was_trigger_phrase_uttered():
    trigger_phrase_uttered()

def set_mic_muted(muted):
  mic = S.obs_get_source_by_name(mic_name)
  if mic is None:
    print(f"Couldn't find the mic by \"{mic_name}\" to be able to mute/unmute it")
  else:
    S.obs_source_set_muted(mic, muted)
    S.obs_source_release(mic)

def trigger_phrase_uttered():
  print("Launching Jump Royale")
  subprocess.Popen(['/Applications/Godot_mono.app/Contents/MacOS/Godot', '--path', '/Volumes/inland/code/JumpRoyale/JumpRoyale'])

  print("Switching OBS scenes to the game")
  set_scene_by_name(scene_name_to_switch_to)

  print("Muting the mic")
  set_mic_muted(True)

def script_unload():
  S.timer_remove(check_for_trigger_phrase)

def main():
  print("Script is running")

  # Make sure we don't have any dangling trigger phrases
  truncate_file(path_to_captions_file)
  S.timer_add(check_for_trigger_phrase, 1000)
  print(f"Timer started to check for phrases: {trigger_phrases}")


main()
