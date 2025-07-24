import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

voices = engine.getProperty('voices')
print(f"Available voices: {[v.name for v in voices]}")

engine.setProperty('voice', voices[0].id)

engine.say("Testing one two three.")
engine.runAndWait()
