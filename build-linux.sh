#!/bin/bash

git clone https://github.com/SantaSpeen/Rcon-VK-Bot.git
cd Rcon-VK-Bot || exit

pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile  --console  --name "Rcon-VK-Bot-LINx64" "./src/main.py"
