#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Autor Wagner Spirigoni, 2010-07-16
# Script de Wake on Lan

import socket
import struct

def WakeOnLan(mac):
# Fazendo checagem do formato do endereço MAC.
    if len(mac) == 12:
        pass
    elif len(mac) == 12 + 5:
        sep = mac[2]
        mac = mac.replace(sep, '')
    else:
        exit()
#        raise ValueError('Formato de endereco MAC incorreto.')
 
# Adicionando a sequencia de MAC
    dados = ''.join(['FFFFFFFFFFFF', mac * 16])
    dados_env = '' 

# Dividir os valores hexadecimais e montar o Magic Packet (pacote utilizado no Wake On Lan)
    for i in range(0, len(dados), 2):
        dados_env = ''.join([dados_env, struct.pack('B', int(dados[i: i + 2], 16))])

# Criando o pacote UDP e enviando na rede
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(dados_env, ('192.168.200.255', 7))
    sock.close()
