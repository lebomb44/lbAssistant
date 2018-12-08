# lbAssistant

Create service file
```shell
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
```
Enable the service
```shel
sudo systemctl enable lbAssistant.service
```
Check the status of the service
```shell
sudo service lbAssistant status
```
Start the service
```shell
sudo service lbAssistant start
```
