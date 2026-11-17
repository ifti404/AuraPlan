Vosk model folder

Extract the contents of your Vosk model into this folder. The structure should
look like this:

  model\am\final.mdl
  model\conf\model.conf
  model\graph\HCLG.fst

Keep the model folder next to AuraPlan.exe. AuraPlan will load it on startup
and use the local microphone for offline voice input. The model is not included
in the initial portable ZIP; add it here before distributing if you want voice
input available immediately.
