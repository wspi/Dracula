#!/usr/bin/env python

import os
import commands
import sys
import string
import time

SERVER="192.168.200.254"
interface = commands.getoutput("ifconfig | grep '192.168.200.' -B1 | head -n1 | awk {'print $1'}")
CLIENTE = commands.getoutput("ifconfig " + interface + " | grep 'inet end' | awk {'print $3'}")

ip = string.split(CLIENTE, ".")
ip = ip[3]

CURSO =  commands.getoutput("netcat " + SERVER + " 500" + ip)
golden = commands.getstatusoutput("echo " + CURSO + " | grep Golden")
log_file = "/home/si/" + CLIENTE + ".log"

def escreve_log(operacao, inicio,  fim,  maquina,  resultado):
    log = open(log_file,  "a")
    msg = str(operacao) + " maquina " + maquina + " iniciou as " + str(inicio) + " e finalizou as " + fim + ". Resultado: " + resultado + "\n"
    log.write(msg)
    log.close()
    os.system("rsync -axv " + log_file + " rsync://" + SERVER + "/logs/" + CURSO + "/" + CLIENTE + ".log")


if golden[0]==0:
    IMAGEM = CURSO
    IMAGEM = string.replace(CURSO, "Golden", "")
    IMAGEM = string.split(IMAGEM, " ")
    IMAGEM = IMAGEM[0]
    CURSO = string.split(IMAGEM, "/")
    CURSO = CURSO[0]

    os.system("dialog --stdout --title 'Receber Imagem' --infobox 'Recebendo imagem " + IMAGEM +"!' 6 40")

    data_inicio =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
    root = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + IMAGEM + "/ / > /tmp/rsync")
    var = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + IMAGEM + "/var/ /var >> /tmp/rsync")
    boot = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + IMAGEM + "/boot/ /boot >> /tmp/rsync")
    log = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + IMAGEM + "/varlog/ /var/log >> /tmp/rsync")
    usr = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + IMAGEM + "/usr/ /usr >> /tmp/rsync")
    home = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + IMAGEM + "/home/ /home >> /tmp/rsync")
    data_fim =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)

else:
    IMAGEM = CURSO + "." + ip

    os.system("dialog --stdout --title 'Receber Imagem' --infobox 'Recebendo imagem " + IMAGEM +"!' 6 40")

    data_inicio =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
    root = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + CURSO + "/" + IMAGEM + "/ / > /tmp/rsync")
    var = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + CURSO + "/" + IMAGEM + "/var/ /var >> /tmp/rsync")
    boot = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + CURSO + "/" + IMAGEM + "/boot/ /boot >> /tmp/rsync")
    log = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + CURSO + "/" + IMAGEM + "/varlog/ /var/log >> /tmp/rsync")
    usr = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + CURSO + "/" + IMAGEM + "/usr/ /usr >> /tmp/rsync")
    home = commands.getstatusoutput("rsync -axv --exclude-from=/home/si/excludes.txt --numeric-ids --delete rsync://" + SERVER + "/cursos/" + CURSO + "/" + IMAGEM + "/home/ /home >> /tmp/rsync")
    data_fim =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)

if root[0]==0 and var[0]==0 and home[0]==0 and boot[0]==0 and log[0]==0 and usr[0]==0:
    os.system("rm -f /etc/udev/rules.d/z25_persistent-net.rules")
    resultado = "Sucesso!"
    os.system("reboot")
else:
    resultado = "Falha!" 



escreve_log("Download", data_inicio,  data_fim, CLIENTE,  resultado)




