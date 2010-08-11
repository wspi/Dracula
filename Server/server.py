#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script feito por Wagner Spirigoni, 2010-07-16

import os
import commands
import sys
import string
from threading import Thread
import time

# adiciona ao Path do Script a Pasta do Script
sys.path.append("/home/si/")

# importa o script de Wake on Lan
import wol

# seta os arquivos utilizados no script

# diretorio onde as pastas dos cursos ficam armazenados
diretorio = "/home/systemimager/"

# arquivo com a lista dos cursos cadastrados
codcursos = "/home/systemimager/.codcursos"

# arquivo que armazena o curso que foi escolhido para enviar ou receber imagens
imagem = "/home/systemimager/.imagem"

# arquivo que armazena as maquinas do range que sera utilizado para enviar e receber imagens
maquinas = "/home/systemimager/.maquinas"

# arquivo de configuracao do dhcp para selecionar os macs das maquinas que serao ligadas pelo Wake On Lan
dhcp = "/etc/dhcp3/dhcpd.conf"

# arquivo de log
log_file = "/home/systemimager/.logs/relatorio.log"



os.system("echo '' > " + imagem)
os.system("echo '' > " + maquinas)

def escreve_log(operacao, inicio,  fim,  maquina,  resultado):
    log = open(log_file,  "a")
    msg = str(operacao) + " maquina " + maquina + " iniciou as " + str(inicio) + " e finalizou as " + fim + ". Resultado: " + resultado + "\n"
    log.write(msg)
    log.close()

def upload():
    todos = commands.getoutput("grep -v 'Golden' " + codcursos + " | cut -d ' ' -f1 ")
    todos= string.split(todos)
    cont = 1
    saida = ""
    
    for i in todos:
        saida = saida + str(i) + " " + str(cont) + " "
        cont = cont + 1
    curso = commands.getstatusoutput("dialog --stdout --menu 'Cursos' 0 0 0 " + saida)
    if curso[0]!=0:
        sys.exit()
    
    curso = curso[1]
    
    REDE=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $2'}")
    a=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $3'}")
    a = int(a)
    b=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $4'}")
    b = int(b)
    
    mac = commands.getoutput("cat " + dhcp + " | grep -v ^# | grep 'hardware ethernet' | awk {'print $3'}")
    mac = string.replace(mac,  ";",  "")
    mac = string.split(mac)

# Liga as maquinas utilizando Wake On Lan
    for i in mac:
        wol.WakeOnLan(i)
    
# Espera as maquinas ligarem
    cont=180
    for i in range(0, 180):
       os.system("dialog --stdout --infobox 'Esperando " + str(cont) + " segundos para as maquinas ligarem' 0 0 ")       
       time.sleep(1)
       cont = cont - 1
    
    # Verifica as maquinas com Rsync Rodando e escreve no arquivo .maquinas
    taxa = 100 / (a + b) +1
    percent = 0
    for i in range(a, (b+1)):
        i = str(i)
        porta = commands.getstatusoutput("nc -z -w2 " + REDE + "." + str(i) + " 873")
        if porta[0]==0:
            os.system("echo '" + REDE + "." + i + " UP on' >> " + maquinas)
        else:
            os.system("echo '" + REDE + "." + i + " DOWN off' >> " + maquinas)

	percent = percent + taxa
	os.system("echo " + str(percent) + " | dialog --stdout --gauge 'Verificando Maquinas' 0 0")

# Variavel que pega as maquinas ativas
    ativas = commands.getstatusoutput("cat " + maquinas + " | grep -v off | wc -l")
    
    if ativas>0:
        selecionados = commands.getstatusoutput("dialog --stdout --title 'Selecine os Micros:' --checklist 'Repita esta operacao ate que o estado do micro desejado esteja UP.' 0 0 0 `cat " + maquinas + "`")
        if selecionados[0]!=0:
            sys.exit()
        selecionados = selecionados[1]
    
    selecionados = string.replace(selecionados, '"', '')
    selecionados = string.split(selecionados)
    
# funcao que faz o rsync para receber as imagens
    def rsync_up(CLIENTE,  MAQUINA):
        data_inicio =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
        root = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/root/ " + diretorio  + curso + "/" + MAQUINA + "/")
        usr = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/usr/ " + diretorio  + curso + "/" + MAQUINA + "/usr/")
        var = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/var/ " + diretorio  + curso + "/" + MAQUINA + "/var/")
        log = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/log/ " + diretorio  + curso + "/" + MAQUINA + "/var/log/")
        home = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/home/ " + diretorio  + curso + "/" + MAQUINA + "/home/")
        boot = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/boot/ " + diretorio  + curso + "/" + MAQUINA + "/boot/")
        data_fim =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
        if root[0] == 0 and usr[0] == 0 and var[0] == 0 and log[0] == 0 and home[0] == 0 and boot[0] == 0:
            resultado = "Sucesso!"
            os.system("netcat " + CLIENTE + " 9091&")
        else:
            resultado = "Falha!"
        
        escreve_log("Upload",  data_inicio,  data_fim, CLIENTE,  resultado)
    
    for i in selecionados:
        CLIENTE = str(i)
        ip = string.split(i, ".")
        ip = ip[3]
        MAQUINA = str(curso) + "." + ip 
# thread para baixar imagens simultaneamente
        th=Thread( target=rsync_up,  args = ( CLIENTE,  MAQUINA,))
        th.start()
    

def download():
    todos = commands.getoutput("ls " + diretorio)
    todos= string.split(todos)
    cont = 1
    saida = ""
    for i in todos:
        saida = saida + str(i) + " " + str(cont) + " "
        cont = cont + 1

    curso = commands.getstatusoutput("dialog --stdout --menu 'Cursos' 0 0 0 " + saida)
    if curso[0]!=0:
        sys.exit()
    curso = curso[1]
    
    golden = commands.getstatusoutput("grep " + curso + " " + codcursos + " | grep 'Golden'")
    if golden[0]==0:
        REDE = "192.168.200"
        a = 1
        b = 12
        os.system("echo '" + curso + " Golden' > " + imagem)
    else:
        os.system("echo " + curso + "> " + imagem)
        REDE=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $2'}")
        a=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $3'}")
        a = int(a)
        b=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $4'}")
        b = int(b)
    
    mac = commands.getoutput("cat " + dhcp + " | grep -v ^# | grep 'hardware ethernet' | awk {'print $3'}")
    mac = string.replace(mac,  ";",  "")
    mac = string.split(mac)

# Liga as maquinas utilizando Wake On Lan
    for i in mac:
       wol.WakeOnLan(i)
    
# Espera as maquinas ligarem
    cont=180
    for i in range(0, 180):
       os.system("dialog --stdout --infobox 'Esperando " + str(cont) + " segundos para as maquinas ligarem' 0 0 ")       
       time.sleep(1)
       cont = cont - 1

# Verifica as maquinas com Rsync Rodando e escreve no arquivo .maquinas

    taxa = 100 / (a + b) +1
    percent = 0
    for i in range(a, (b+1)):
        i = str(i)
        porta = commands.getstatusoutput("nc -z -w2 " + REDE + "." + str(i) + " 873")
        if porta[0]==0:
            os.system("echo '" + REDE + "." + i + " UP on' >> " + maquinas)
        else:
            os.system("echo '" + REDE + "." + i + " DOWN off' >> " + maquinas)

	percent = percent + taxa
	os.system("echo " + str(percent) + " | dialog --stdout --gauge 'Verificando Maquinas' 0 0")

# Variavel que pega as maquinas ativas
    ativas = commands.getstatusoutput("cat " + maquinas + " | grep -v off | wc -l")
    
    if ativas>0:
        selecionados = commands.getstatusoutput("dialog --stdout --title 'Selecine os Micros:' --checklist 'Repita esta operacao ate que o estado do micro desejado esteja UP.' 0 0 0 `cat " + maquinas + "`")
        if selecionados[0]!=0:
            sys.exit()
        selecionados = selecionados[1]
    
    selecionados = string.replace(selecionados, '"', '')
    selecionados = string.split(selecionados)
    
    os.system("rsync --daemon --config=/etc/server_rsyncd.conf --port 873")

    for i in selecionados:
        ip = string.split(i, ".")
        ip = ip[3]
        os.system("netcat -l -p 500" + ip + " -c 'cat " + imagem + "'&")
        os.system("netcat " + i + " 9090&")

def up_down():
    todos_up = commands.getoutput("grep -v 'Golden' " + codcursos + " | cut -d ' ' -f1 ")
    todos_up= string.split(todos_up)
    cont = 1
    saida_up = ""
    for i in todos_up:
        saida_up = saida_up + str(i) + " " + str(cont) + " "
        cont = cont + 1
    
    todos_down = commands.getoutput("ls " + diretorio)
    todos_down = string.split(todos_down)
    cont = 1
    saida_down = ""
    for i in todos_down:
        saida_down = saida_down + str(i) + " " + str(cont) + " "
        cont = cont + 1

    curso_up = commands.getstatusoutput("dialog --stdout --menu 'Selecione o Curso a ser recebido:' 0 0 0 " + saida_up)
    if curso_up[0]!=0:
        sys.exit()
    
    curso_up = curso_up[1]
    
    curso_down = commands.getstatusoutput("dialog --stdout --menu 'Selecione o Curso a ser enviado:' 0 0 0 " + saida_down)
    if curso_down[0]!=0:
        sys.exit()
    
    curso_down = curso_down[1]
    golden = commands.getstatusoutput("grep " + curso_down + " " + codcursos + " | grep 'Golden'")
    if golden[0]==0:
        REDE = "192.168.200"
        a = 1
        b = 12
        os.system("echo '" + curso_down + " Golden' > " + imagem)
    else:
        os.system("echo " + curso_down + "> " + imagem)
        REDE=commands.getoutput("grep " + curso_down + " " + codcursos + " | awk {'print $2'}")
        a=commands.getoutput("grep " + curso_down + " " + codcursos + " | awk {'print $3'}")
        a = int(a)
        b=commands.getoutput("grep " + curso_down + " " + codcursos + " | awk {'print $4'}")
        b = int(b)
    os.system("echo " + curso_down + "> " + imagem)
    os.system("rsync --daemon --config=/etc/server_rsyncd.conf --port 873")
    
    mac = commands.getoutput("cat " + dhcp + " | grep -v ^# | grep 'hardware ethernet' | awk {'print $3'}")
    mac = string.replace(mac,  ";",  "")
    mac = string.split(mac)

# Liga as maquinas utilizando Wake On Lan
    for i in mac:
        wol.WakeOnLan(i)
    
# Espera as maquinas ligarem
    cont=180
    for i in range(0, 180):
       os.system("dialog --stdout --infobox 'Esperando " + str(cont) + " segundos para as maquinas ligarem' 0 0 ")       
       time.sleep(1)
       cont = cont - 1

# Verifica as maquinas com Rsync Rodando e escreve no arquivo .maquinas
    taxa = 100 / (a + b) +1
    percent = 0
    for i in range(a, (b+1)):
        i = str(i)
        porta = commands.getstatusoutput("nc -z -w2 " + REDE + "." + str(i) + " 873")
        if porta[0]==0:
            os.system("echo '" + REDE + "." + i + " UP on' >> " + maquinas)
        else:
            os.system("echo '" + REDE + "." + i + " DOWN off' >> " + maquinas)

	percent = percent + taxa
	os.system("echo " + str(percent) + " | dialog --stdout --gauge 'Verificando Maquinas' 0 0")

# Variavel que pega as maquinas ativas
    ativas = commands.getstatusoutput("cat " + maquinas + " | grep -v off | wc -l")
    
    if ativas>0:
        selecionados = commands.getstatusoutput("dialog --stdout --title 'Selecine os Micros:' --checklist 'Repita esta operacao ate que o estado do micro desejado esteja UP.' 0 0 0 `cat " + maquinas + "`")
        if selecionados[0]!=0:
            sys.exit()
    
        selecionados = selecionados[1]
    
    selecionados = string.replace(selecionados, '"', '')
    selecionados = string.split(selecionados)
    
# funcao que faz o rsync para receber as imagens
    def rsync_up(CLIENTE,  IP):
        MAQUINA= str(curso_up) + "." + IP
        data_inicio =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
        root = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/root/ " + diretorio  + curso_up + "/" + MAQUINA + "/")
        usr = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/usr/ " + diretorio  + curso_up + "/" + MAQUINA + "/usr/")
        var = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/var/ " + diretorio  + curso_up + "/" + MAQUINA + "/var/")
        log = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/log/ " + diretorio  + curso_up + "/" + MAQUINA + "/var/log/")
        home = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/home/ " + diretorio  + curso_up + "/" + MAQUINA + "/home/")
        boot = commands.getstatusoutput("rsync --numeric-ids -axv --delete rsync://" + CLIENTE + "/boot/ " + diretorio  + curso_up + "/" + MAQUINA + "/boot/")
        data_fim =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
        if root[0] == 0 and usr[0] == 0 and var[0] == 0 and log[0] == 0 and home[0] == 0 and boot[0] == 0:
            resultado = "Sucesso!"
            os.system("netcat -l -p 500" + IP + " -c 'cat " + imagem + "'&")
            os.system("netcat " + CLIENTE + " 9090&")
        else:
            resultado = "Falha!"
        
        escreve_log("Upload e Download",  data_inicio,  data_fim, CLIENTE,  resultado)
    
    for i in selecionados:
        CLIENTE = str(i)
        ip = string.split(i, ".")
        ip = ip[3]
# thread para baixar imagens simultaneamente
        th=Thread( target=rsync_up,  args = ( CLIENTE,  ip,))
        th.start()

def envia_uma():
    todos = commands.getoutput("cut -d ' ' -f1 " + codcursos + " | grep -v 'Golden'")
    todos= string.split(todos)
    cont = 1
    saida = ""
    
    for i in todos:
        saida = saida + str(i) + " " + str(cont) + " "
        cont = cont + 1
    curso = commands.getstatusoutput("dialog --stdout --menu 'Cursos' 0 0 0 " + saida)
    if curso[0]!=0:
        sys.exit()
    
    curso = curso[1]
    
    imagens = commands.getoutput("ls " + diretorio + "/" + curso)
    todos = string.split(imagens)
    cont = 1
    saida = ""
    
    for i in todos:
        saida = saida + str(i) + " " + str(cont) + " "
        cont = cont + 1
    imagens = commands.getstatusoutput("dialog --stdout --menu 'Cursos' 0 0 0 " + saida)
    if imagens[0]!=0:
        sys.exit()
    imagens = imagens[1]
    
    REDE=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $2'}")
    a=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $3'}")
    a = int(a)
    b=commands.getoutput("grep " + curso + " " + codcursos + " | awk {'print $4'}")
    b = int(b)
    
    mac = commands.getoutput("cat " + dhcp + " | grep -v ^# | grep 'hardware ethernet' | awk {'print $3'}")
    mac = string.replace(mac,  ";",  "")
    mac = string.split(mac)
    
    # Liga as maquinas utilizando Wake On Lan
    for i in mac:
       wol.WakeOnLan(i)
    
# Espera as maquinas ligarem
    cont=180
    for i in range(0, 180):
       os.system("dialog --stdout --infobox 'Esperando " + str(cont) + " segundos para as maquinas ligarem' 0 0 ")       
       time.sleep(1)
       cont = cont - 1

# Verifica as maquinas com Rsync Rodando e escreve no arquivo .maquinas

    taxa = 100 / (a + b) +1
    percent = 0
    for i in range(a, (b+1)):
        i = str(i)
        porta = commands.getstatusoutput("nc -z -w2 " + REDE + "." + str(i) + " 873")
        if porta[0]==0:
            os.system("echo '" + REDE + "." + i + " UP on' >> " + maquinas)
        else:
            os.system("echo '" + REDE + "." + i + " DOWN off' >> " + maquinas)

	percent = percent + taxa
	os.system("echo " + str(percent) + " | dialog --stdout --gauge 'Verificando Maquinas' 0 0")

# Variavel que pega as maquinas ativas
    ativas = commands.getstatusoutput("cat " + maquinas + " | grep -v off | wc -l")
    
    if ativas>0:
        selecionados = commands.getstatusoutput("dialog --stdout --title 'Selecine os Micros:' --checklist 'Repita esta operacao ate que o estado do micro desejado esteja UP.' 0 0 0 `cat " + maquinas + "`")
        if selecionados[0]!=0:
            sys.exit()
        selecionados = selecionados[1]
    
    selecionados = string.replace(selecionados, '"', '')
    selecionados = string.split(selecionados)
    
    os.system("echo '" + curso + "/" + imagens + " Golden' > " + imagem)
    os.system("rsync --daemon --config=/etc/server_rsyncd.conf --port 873")

    for i in selecionados:
        ip = string.split(i, ".")
        ip = ip[3]
        os.system("netcat -l -p 500" + ip + " -c 'cat " + imagem + "'&")
        os.system("netcat " + i + " 9090&")

def golden():
    nome = commands.getstatusoutput("dialog --stdout --title 'Criar Golden' --inputbox 'Digite o nome da imagem:' 9 25")
    if nome[0]!=0:
        sys.exit()
    nome = nome[1]	
    busca = commands.getstatusoutput("grep " + nome + " " + codcursos)
    if busca[0]==0:
        os.system("dialog --stdout --title 'Erro' --infobox 'Imagem já existe!' 0 0")
        sys.exit()
    
    REDE = "192.168.200"
    a = 1
    b = 12
    
    # Verifica as maquinas com Rsync Rodando e escreve no arquivo .maquinas

    taxa = 100 / (a + b) +1
    percent = 0
    for i in range(a, (b+1)):
        i = str(i)
        porta = commands.getstatusoutput("nc -z -w2 " + REDE + "." + str(i) + " 873")
        if porta[0]==0:
            os.system("echo \"" + REDE + "." + i + " UP ''\" >> " + maquinas)
        else:
            os.system("echo \"" + REDE + "." + i + " DOWN ''\" >> " + maquinas)

	percent = percent + taxa
	os.system("echo " + str(percent) + " | dialog --stdout --gauge 'Verificando Maquinas' 0 0")

# Variavel que pega as maquinas ativas
    ativas = commands.getstatusoutput("cat " + maquinas + " | grep -v off | wc -l")
    
    if ativas>0:
        selecionados = commands.getstatusoutput("dialog --stdout --title 'Selecione a Maquina para a Golden:' --radiolist 'Repita esta operacao ate que o estado do micro desejado esteja UP.' 0 0 0 `cat " + maquinas + "`")
        if selecionados[0]!=0:
            sys.exit()
        selecionados = selecionados[1]
    
    selecionados = string.replace(selecionados, '"', '')
    selecionados = string.split(selecionados)
     
     
    os.system("mkdir " + diretorio + nome)
    
    os.system("echo " + nome + " Golden >> " + codcursos)
    os.system("mkdir " + diretorio + ".logs/" + nome)

    for i in selecionados:
        CLIENTE = str(i)
	data_inicio =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
   	root = commands.getstatusoutput("rsync --exclude-from=/home/si/excludes.txt --numeric-ids -axv --delete rsync://" + CLIENTE + "/root/ " + diretorio + nome + "/")
   	usr = commands.getstatusoutput("rsync --exclude-from=/home/si/excludes.txt --numeric-ids -axv --delete rsync://" + CLIENTE + "/usr/ " + diretorio + nome + "/usr/")
   	var = commands.getstatusoutput("rsync --exclude-from=/home/si/excludes.txt --numeric-ids -axv --delete rsync://" + CLIENTE + "/var/ " + diretorio + nome + "/var/")
   	log = commands.getstatusoutput("rsync --exclude-from=/home/si/excludes.txt --numeric-ids -axv --delete rsync://" + CLIENTE + "/log/ " + diretorio + nome + "/var/log/")
   	home = commands.getstatusoutput("rsync --exclude-from=/home/si/excludes.txt --numeric-ids -axv --delete rsync://" + CLIENTE + "/home/ " + diretorio + nome + "/home/")
   	boot = commands.getstatusoutput("rsync --exclude-from=/home/si/excludes.txt --numeric-ids -axv --delete rsync://" + CLIENTE + "/boot/ " + diretorio + nome + "/boot/")
   	data_fim =  str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" +  str(time.localtime().tm_year) + " - " + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec)
   	if root[0] == 0 and usr[0] == 0 and var[0] == 0 and log[0] == 0 and home[0] == 0 and boot[0] == 0:
       	    resultado = "Sucesso!"
            os.system("netcat " + CLIENTE + " 9091&")
   	else:
            resultado = "Falha!"
        
   	escreve_log("Golden",  data_inicio,  data_fim, CLIENTE,  resultado)
    

def adiciona():
    codigo = commands.getstatusoutput("dialog --stdout --title 'Adicionar Curso' --inputbox 'Digite o codigo do curso:' 9 25 ")
    if codigo[0]!=0:
        sys.exit()
    
    instrutor = commands.getstatusoutput("dialog --stdout --title 'Adicionar Curso' --inputbox 'Digite o nome do instrutor:' 9 25")
    if instrutor[0]!=0:
        sys.exit()
    
    periodo = commands.getstatusoutput("dialog --stdout --title 'Adicionar Curso' --menu 'Escolha o periodo do curso:' 0 0 0 'Diurno' 1 'Noturno' 2 'Domingo' 3 'Sabado' 4")
    if periodo[0]!=0:
        sys.exit()
    
    curso = str(codigo[1]) + "." + str(instrutor[1] + "." + periodo[1])
    busca = commands.getstatusoutput("grep " + curso + " " + codcursos)
    if busca[0]==0:
        os.system("dialog --stdout --title 'Erro' --infobox 'Curso já existe!' 0 0")
        sys.exit()
    
    ip = commands.getstatusoutput("dialog --stdout --title 'Adicionar Curso' --inputbox 'Digite a faixa de IP:' 9 25 192.168.200" )
    if ip[0]!=0:
        sys.exit()
    
    intervalo = commands.getstatusoutput("dialog --stdout --title 'Adicionar Curso' --inputbox 'Digite o intervalo de IPS (1-254) :' 9 25 1-12")
    if intervalo[0]!=0:
        sys.exit()
    
    ip = str(ip[1])
    intervalo = str(intervalo[1])
    intervalo = string.replace(intervalo,  "-",  " ")
    
    dircurso = diretorio + curso
    
    os.system("echo " + curso + " " + ip + " " + intervalo + " >> "+ codcursos)
    os.system("mkdir " + dircurso)
    
    os.system("mkdir " + diretorio + ".logs/" + curso)    
    
    intervalo = string.split(intervalo)
    
    int1 = int(intervalo[0])
    int2 = int(intervalo[1])
    
    
    for i in range(int1,  (int2 +1)):
        i = str(i)
        os.system("mkdir " + dircurso + "/" + curso + "." + i)
        
    os.system("dialog --stdout --title 'Adicionar Curso' --msgbox 'O nome do curso adicionado e " + curso + "' 0 0")
    


    

def remove():
    cadastro = commands.getoutput("cut -d ' ' -f1 " + codcursos)
    
    if cadastro=="":
        os.system("dialog --stdout --title 'Remover Curso' --msgbox 'Nao existe nenhum curso cadastrado' 0 0")
        sys.exit()
    
    todos = commands.getoutput("cut -d ' ' -f1 " + codcursos)
    todos= string.split(todos)
    cont = 1
    saida = ""
    for i in todos:
        saida = saida + str(i) + " " + str(cont) + " "
        cont = cont + 1
    
    curso = commands.getstatusoutput("dialog --stdout --menu 'Remover Curso' 0 0 0 " + saida)
    if curso[0]!=0:
        sys.exit()
    

    
    curso = curso[1]
    

    
    confirm = commands.getstatusoutput("dialog --stdout --yesno 'Deseja REALMENTE excluir as imagens do curso " + curso + "?' 0 0")
    if confirm[0]!=0:
        sys.exit()
    
    remover = commands.getstatusoutput("rm -rf " + diretorio + curso + " " + diretorio + ".logs/" + curso)
    if remover[0]!=0:
        os.system("dialog --stdout --title 'Remover Curso' --msgbox 'Erro ao remover curso' 0 0")
        sys.exit()
    else:
        os.system("grep -v " + curso + " " + codcursos + " > /tmp/codcursos")
        os.system("mv /tmp/codcursos " + codcursos)
        os.system("dialog --stdout --title 'Remover Curso' --msgbox 'Curso removido com sucesso' 0 0")
        
    


# menu de opcoes
escolha = commands.getoutput("dialog --stdout --title 'SYSTEM IMAGER' --menu 'Escolha uma das opcoes:' 0 0 0 1 'Receber Imagens' 2 'Enviar Imagens' 3 'Receber e Enviar' 4 'Enviar apenas uma imagem para toda sala' 5 'Criar Imagem Golden' 6 'Adicionar curso' 7 'Remover curso'")

if escolha=="1":
    upload()
elif escolha=="2":
    download()
elif escolha=="3":
    up_down()
elif escolha=="4":
    envia_uma()	   
elif escolha=="5":
    golden()
elif escolha=="6":
    adiciona()
elif escolha=="7":
   remove()
