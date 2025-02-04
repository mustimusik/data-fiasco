from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from datasets import Audio, Dataset
import torch
from tqdm.auto import tqdm

processor = Wav2Vec2Processor.from_pretrained("asr_processor")
model = Wav2Vec2ForCTC.from_pretrained("asr_model")

dataset = Dataset.from_dict({"audio":["piano_3_Cn_j_f_00.wav", "piano_3_Ef_a_m_02.wav", "full_song.wav", "piano_3_Cn_j_f_00_&_piano_3_Ef_a_m_02.mp3", "1.mp3"]})
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

splitted = []
example = dataset[4]["audio"]
shape = example["array"].shape[0]
for i in tqdm(range(0, shape, 32000)):
    if i+32000 < shape:
        data = example["array"][i:i+32000]
    else:
        data = example["array"][i:]
    splitted.append(data)

for i in range(len(splitted)):
    inputs = processor(splitted[i], sampling_rate=16000).input_values[0]
    with torch.no_grad():
        input_values = torch.tensor(inputs).unsqueeze(0)
        logits = model(input_values).logits

        pred_ids = torch.argmax(logits, dim=-1)
        hasil = processor.batch_decode(pred_ids)
        print(hasil)
            
    # if conf >= 0.50:
    #     print(i, conf[0].item(), classes[0].item(), model.config.id2label[classes[0].item()])
    # else:
    #     print(i, "break")


# pre = processor(dataset[0]["audio"]["array"], sampling_rate=16000).input_values[0]
# with torch.no_grad():
#     input_values = torch.tensor(pre).unsqueeze(0)
#     logits = model(input_values).logits

# pred_ids = torch.argmax(logits, dim=-1)
# hasil = processor.batch_decode(pred_ids)
# print(hasil)
