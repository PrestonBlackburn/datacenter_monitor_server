# Rasberry Pi Meshtastic Setup

## Required/Used Parts
- Rasberry Pi 4/5
- Pico Pi (or other device with meshtastic installed)

## Setup 
Use the rasberry pi installer to format the micro sd card with the ubuntu server image  
- [Raspberry Pi Installer](https://www.raspberrypi.com/software/)
- [Ubuntu Server](https://ubuntu.com/download/server) *version 26*

*Optional* 
- [log2ram](https://github.com/azlux/log2ram) - For helping MicroSD card longevity


## Meshtastic Setup
**eventually I'll probably have a single container do all of this**
from user dir - 
```bash
mkdir project
cd project
apt install python3.14-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade "meshtastic[cli]"
```

Check install
```bash
meshtastic -v
```

Test connection:
```bash
meshtastic --port /dev/ttyUSB1 --noproto
meshtastic --port /dev/ttyACM0 --noproto
```


Create new private channels:


<!-- lsof /dev/ttyUSB2
kill 784958 -->
```bash
# clear old channels (optional)
meshtastic --port /dev/ttyUSB2 --factory-reset
meshtastic --port /dev/ttyACM0 --factory-reset
# note - had to install 2.6.x firmware on meshtastic to avoid wire protocol issue

# create new channel
python create_test_channel.py

# set new channel - 
meshtastic --port /dev/ttyUSB1 --set channel_index 1 channel_num 1
```


**Migrate from local testing to server**  
Dump data:
```bash
docker run --rm -it --network host --env-file .env_pg -v "$(pwd)":/backup --entrypoint pg_dump postgres:18 -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -f /backup/local-backup-$(date +%Y%m%d).dump
```

Restore data:
```bash
docker run --rm -it --env-file .env_remote -v "$(pwd)":/backup --entrypoint pg_restore postgres:18 -h postgres.lan -p 5432 -U "$POSTGRES_USER" -d sensors --clean --if-exists /backup/local-backup-20260616.dump
```

**Run script in background**  
setup env vars and source `.env` file  


(also may need to update dialout permissions)  
```bash
sudo usermod -a -G dialout $USER
```

Run consumer script in the background
```bash
nohup python -u consumer.py > output.log 2>&1 &
```
