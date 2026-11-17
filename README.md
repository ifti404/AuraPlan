# AuraPlan Application

Download the Windows x64 portable app:

[AuraPlan portable ZIP](https://github.com/ifti404/AuraPlan/raw/refs/heads/Application/release/AuraPlan-portable.zip)

## Run it

1. Download and extract the ZIP.
2. Keep the extracted `AuraPlan` folder together.
3. Run `AuraPlan.exe` from that folder. Python does not need to be installed.

The bundle includes the Python runtime and app dependencies. Tasks and profiles
are stored in the `data` folder beside the executable, so the extracted folder
can be kept on a USB drive.

## Optional Vosk voice model

The speech-recognition runtime is included, but the large Vosk language model
is not. To enable offline voice capture, put the extracted model files in the
`model` folder beside `AuraPlan.exe`, with this structure:

```text
model\am\final.mdl
model\conf\model.conf
model\graph\HCLG.fst
```

Without a model, task planning and management still work; voice capture stays
disabled.
