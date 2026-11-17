Vosk model folder

Place the extracted contents of your Vosk model in this folder. AuraPlan
expects the model's am, conf, and graph folders directly under model, including
am\final.mdl, conf\model.conf, and graph\HCLG.fst.

When you build AuraPlan, build_windows.ps1 copies this folder into the portable
bundle beside AuraPlan.exe. Large model files stay out of source control.
