import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
from datasets import Audio, Dataset
from tqdm.auto import tqdm

feature_extractor = AutoFeatureExtractor.from_pretrained("sec1-144label-volume")
model = AutoModelForAudioClassification.from_pretrained("sec1-144label-volume")

dataset = Dataset.from_dict({
    "audio":[
        "piano_3_Cn_j_f_00.wav", 
        "piano_3_Ef_a_m_02.wav", 
        "full_song.wav", 
        "piano_3_Cn_j_f_00_&_piano_3_Ef_a_m_02.mp3", 
        "1.wav",
        "2.mp3"
    ]
})
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

splitted = []
example = dataset[0]["audio"]
shape = example["array"].shape[0]

for i in tqdm(range(0, shape, 16000)):
    if i+16000 < shape:
        data = example["array"][i:i+16000]
    else:
        data = example["array"][i:]
    splitted.append(data)

for i in range(len(splitted)):
    inputs = feature_extractor(splitted[i], sampling_rate=16000, return_tensors="pt", max_length=16000, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1)
        conf, classes = torch.max(probs, 1)
        predicted_class_ids = torch.argmax(logits).item()
        predicted_label = model.config.id2label[predicted_class_ids]
    
    if conf >= 0.70:
        print(i, conf[0].item(), classes[0].item(), model.config.id2label[classes[0].item()])
    else:
        print(i, "break")
