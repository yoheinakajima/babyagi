# BabyAGI4All

A small autonomous AI agent based on [BabyAGI](https://github.com/yoheinakajima/babyagi) by Yohei Nakajima.
</br>

Runs on CPU with the [GPT4All](https://github.com/nomic-ai/gpt4all) model by Nomic AI.
</br>

100% open source, 100% local, no API-keys needed.
</br>

# Installation:

1. Clone this repository
2. Install the requirements: *pip install -r requirements.txt*
3. Download a model file (see below)
4. Copy the file *.env.example* to *.env*
4. Edit the model-path and other preferences in the file *.env*
</br>

# Model Downloads

The following model files have been tested successfully:

* *gpt4all-lora-quantized-ggml.bin*
* *ggml-wizardLM-7B.q4_2.bin*
* *ggml-vicuna-7b-1.1-q4_2.bin*

Some of these model files can be downloaded from [here](https://github.com/nomic-ai/gpt4all-chat#manual-download-of-models)
</br>

Then run *python babyagi.py*

Have fun!
</br>
