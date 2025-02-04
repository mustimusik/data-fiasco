import pandas as pd
import os
from tqdm.auto import tqdm

base_path = "audioPianoTriadDataset/audioPianoTriadDataset/audio_augmented_x10"
files = os.listdir(base_path)

metadata = pd.DataFrame({"file_name":files})
transcriptions = []
for fl in tqdm(files):
    file_name = fl.split("_")
    file_name.pop()
    file_name.pop()
    name = "_".join(file_name)
    transcriptions.append(name)
metadata["transcription"] = transcriptions
metadata.to_csv("metadata.csv", index=False)
    
    
    