############################################################################################# 
IDENTIFICAÇÃO DO GRUPO                                                                     
############################################################################################
GRUPO - 04
55853 - Madalena Rodrigues
56897 - Pedro Almeida
56935 - Rómulo Nogueira
############################################################################################
# LISTA DE IMPORTS                                                                         
############################################################################################
# pgrepwc: 
import sys, os, argparse
import re, functools
import time, signal
from multiprocessing import Process, Value, Lock, Array, Pipe
from datetime import datetime
import pickle

# hpgrepwc: 
import sys, argparse
import pickle 
import datetime
############################################################################################
# EXEMPLOS DE EXECUÇÃO
############################################################################################
python3 pgrepwc.py pgrepwc -l Sistemas -f file2.txt
python3 pgrepwc.py pgrepwc -c Sistemas Operativos -f file3.txt 
python3 pgrepwc.py pgrepwc -a -l  -w 1 Sistemas -f file4.txt 
python3 pgrepwc.py pgrepwc -a -c Sistemas -f file4.txt 

python3 pgrepwc.py pgrepwc -c -o outfile.bin Sistemas Operativos -f file2.txt file3.txt file4.txt
python3 hpgrepwc.py hpgrepwc outfile.bin

python3 pgrepwc.py pgrepwc -l -w 1 -o outfile2.bin Michael Project -f file2.txt file3.txt file4.txt
python3 hpgrepwc.py hpgrepwc outfile2.bin

python3 pgrepwc.py pgrepwc -a -l Sistemas Operativos -p 1 -f file2.txt file4.txt

python3 pgrepwc.py pgrepwc -l -o outfile3.bin Michael -p 5 -f file2.txt file3.txt file4.txt
python3 hpgrepwc.py hpgrepwc outfile3.bin

python3 pgrepwc.py pgrepwc -a -c -o -w 1 outfile4.bin Sistemas -p 3 -f file2.txt file3.txt file4.txt
python3 hpgrepwc.py hpgrepwc outfile4.bin

python3 pgrepwc.py pgrepwc -c -p 5 -w 1 -o outfile5.bin Sistemas Project Michael -f file2.txt file3.txt file4.txt
python3 hpgrepwc.py hpgrepwc outfile5.bin
############################################################################################
# INFORMAÇÃO ADICIONAL
############################################################################################

Há semelhança da primeira entrega não conseguimos processar o file1.txt dado pela professora, devido a:
-> Crash da VM
-> Erros como por exemplo: killed logo após a execução e memoryError
