# lbAssistant

sudo vi /lib/systemd/system/lbAssistant.service
[Unit]
Description=My awesome assistant app

[Service]
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=/bin/bash -c 'python3 -u lbAssistant.py'
WorkingDirectory=/home/pi
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

sudo systemctl enable lbAssistant.service
sudo service lbAssistant status
sudo service lbAssistant start
sudo service lbAssistant stop

