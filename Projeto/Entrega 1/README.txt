###################################################################################################################
# IDENTIFICAÇÃO DO GRUPO                                                                                          #
###################################################################################################################
GRUPO - 04
55853 - Madalena Rodrigues
56897 - Pedro Almeida
56935 - Rómulo Nogueira

###################################################################################################################
# LISTA DE IMPORTS                                                                                                #
###################################################################################################################
import sys    
import os      
import argparse    
import re
import unicodedata 

# Processos 
from multiprocessing import Process, Value 

# Threads
from threading import Thread

###################################################################################################################
# EXEMPLOS DE EXECUÇÃO                                                                                            #
###################################################################################################################
# Processos:
python3 pgrepwc.py pgrepwc -c palavras -f ficheiros
python3 pgrepwc.py pgrepwc -l palavras -f ficheiros
python3 pgrepwc.py pgrepwc -a -c palavras -f ficheiros
python3 pgrepwc.py pgrepwc -a -l palavras -f ficheiros

python3 pgrepwc.py pgrepwc -c -p n palavras -f ficheiros
python3 pgrepwc.py pgrepwc -l -p n palavras -f ficheiros
python3 pgrepwc.py pgrepwc -a -c -p n palavras -f ficheiros
python3 pgrepwc.py pgrepwc -a -l -p n palavras -f ficheiros

python3 pgrepwc.py pgrepwc -a -l -c palavras -f ficheiros -> Vai dar erro


# Threads:
python3 pgrepwc_threads.py pgrepwc -c palavras -f ficheiros
python3 pgrepwc_threads.py pgrepwc -l palavras -f ficheiros
python3 pgrepwc_threads.py pgrepwc -a -c palavras -f ficheiros
python3 pgrepwc_threads.py pgrepwc -a -l palavras -f ficheiros

python3 pgrepwc_threads.py pgrepwc -c -p n palavras -f ficheiros
python3 pgrepwc_threads.py pgrepwc -l -p n palavras -f ficheiros
python3 pgrepwc_threads.py pgrepwc -a -c -p n palavras -f ficheiros
python3 pgrepwc_threads.py pgrepwc -a -l -p n palavras -f ficheiros

python3 pgrepwc_threads.py pgrepwc -a -l -c palavras -f ficheiros -> Vai dar erro

###################################################################################################################
# INFORMAÇÃO ADICIONAL                                                                                            #
###################################################################################################################

relatar a informação que acharem pertinente sobre a sua implementação do projeto (ex., limitações, qual a abordagem usada para a divisão dos ficheiros pelos processos).

# Foi utilizado o seguinte código (retirado da internet) para testar o funcionamento das threads:

import ctypes
libc = ctypes.cdll.LoadLibrary('libc.so.6')

SYS_gettid = 186

def getThreadId():
   """Returns OS thread id - Specific to Linux"""
   return libc.syscall(SYS_gettid)

# E onde queríamos ver qual o TID colocávamos a seguinte linha:
print("TID = " + str(getThreadId()))


# COMO FUNCIONA O PROGRAMA

A divisão dos ficheiros foi feita através da função parte lista, que recebia uma lista de ficheiros
e dividia dependendo do número de processos a criar em listas de listas com os ficheiros
EXPLICAR MELHOR
exemplo:
[ficheiro1, ficheiro2, ficheiro3, ficheiro4, ficheiro5] 
3 processos filhos

[[ficheiro1, ficheiro4], [ficheiro2, ficheiro5], [ficheiro3]]









