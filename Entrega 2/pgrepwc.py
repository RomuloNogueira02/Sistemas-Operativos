###################################################################################################################
# LISTA DE IMPORTS                                                                                                #
###################################################################################################################
import sys, os, argparse
import re, functools
import time, signal
from multiprocessing import Process, Value, Lock, Array, Pipe
from datetime import datetime
import pickle


sinal_terminar = False

def terminaFilho(signum, NULL):
    """ 
    Função que recebe o sinal SIGINT emitido pelo pai e altera o valor da variável para sinal_terminar
    para True 
    Args:
        signum (sinal): Signal handler
        NULL (frame)
    """
    print("terminar filho")
    global sinal_terminar
    sinal_terminar = True

####################################################################################################################
# Definição das variáveis                                                                                          #
####################################################################################################################

inicio = time.time()
dataInicial = datetime.now()

listaOcorrencias = []
listaDeFicheiros = []

tempoAlarmes = 0

pipe_pai, pipe_filho = Pipe()

contadorDeOcorrencias = Value("i", 0)
contadorDeLinhas = Value("i", 0)
mutex = Lock()


nP = []
listaProcessos = []
procs = []
estadoProcesso = []

linhasProcessadas = Value("i", 0)

###################################################################################################################
# FUNÇÕES AUXILIARES                                                                                              #
###################################################################################################################


def leFicheiro(ficheiro): 
    """ 
    Cria uma lista onde estão todas as linhas do ficheiro enumeradas 
    Args:
        ficheiro(str): nome do ficheiro que se pretende ler 
    Returns:
        linhas(list): lista de tuplos com as linhas do ficheiro enumeradas 
        em que cada tuplo tem a forma: (1, conteúdo da linha numero 1)
    """
    resultado = []
    with open(ficheiro, 'r', encoding='utf8') as ficheiroTexto:
        for linha in ficheiroTexto:
            resultado.append(linha) 
    resultado = list(map(lambda linha: linha.strip('\n'), resultado))       
    return resultado


def escreveParaBin(ficheiro, dados):
    """ 
    Cria uma lista onde estão todas as linhas do ficheiro enumeradas 
    Args:
        ficheiro (str): nome do ficheiro onde se pretende escrever os dados 
        dados (List): lista com as informações que irão ser guardadas no ficheiro 
    """
    with open(ficheiro,"wb") as outFile: 
        pickle.dump(dados, outFile)


##################################################################################################################

def constroiRegex(listaPalavras):
    """
    Função que a partir de uma lista de palavras constrói uma expressão regular apropriada
    Args:
        listaPalavras (List): Lista de palavras
    Returns:
        String: Regular expression apropriada
    """
    regex = ""
    for i in range(len(listaPalavras) - 1):
        regex = regex + listaPalavras[i] + "|"   
    return r"\b(" + regex + listaPalavras[-1] + r")\b"


##################################################################################################################

def particaoJusta(listaFicheiros, nProcessos):
    """
    Função que faz a partição dos ficheiros de forma justa para cada processos, partição feita pelo numero de linhas não nulas
    Args:
        listaFicheiros (List): Lista de ficheiros 
        nProcessos (int): nº de processos criados
    Returns:
        Lista de lista de linhas que cada processo vai processar
        
    """
    ficheirosLidos = [leFicheiro(ficheiro) for ficheiro in listaFicheiros]
    ficheirosFiltrados = [list(filter(lambda linha: linha != "", ficheiro)) for ficheiro in ficheirosLidos] # Retira as linhas vazias
    numeroLinhasPorFicheiro = list(map(lambda ficheiro: len(ficheiro), ficheirosFiltrados)) # Faz o número total de linhas
    numeroTotalDeLinhas = sum(numeroLinhasPorFicheiro)
    linhasPorProcesso = numeroTotalDeLinhas//nProcessos
    sobra = numeroTotalDeLinhas % nProcessos
    
    lista = list(map(lambda i: linhasPorProcesso*(i+1), range(nProcessos)))
    
    lista[-1] += sobra 
    
    listaLinhas = functools.reduce(lambda x,y :x+y , ficheirosFiltrados)

    quase_final = [listaLinhas[:lista[0]]] + list(map(lambda indice: listaLinhas[lista[indice]: lista[indice + 1]], range(len(lista) - 1)))
    
    i = 0
    j = 0
    final = []
    res = []


    while i < len(quase_final) and j < len(numeroLinhasPorFicheiro):    
        if len(quase_final[i]) < numeroLinhasPorFicheiro[j]:
            res.append(quase_final[i])
            numeroLinhasPorFicheiro[j] -= len(quase_final[i])
            i += 1
            final.append(res)
            res = []

        elif len(quase_final[i]) == numeroLinhasPorFicheiro[j]:
            res.append(quase_final[i])
            numeroLinhasPorFicheiro[j] = 0
            i += 1
            j += 1
            final.append(res)
            res = []

        elif len(quase_final[i]) > numeroLinhasPorFicheiro[j]:
            res.append(quase_final[i][:numeroLinhasPorFicheiro[j]])
            quase_final[i] = quase_final[i][numeroLinhasPorFicheiro[j]:]
            j += 1
    return final


###################################################################################################################

def auxDeContagem(lista, linhasPorFicheiro, palavras, flagC):
    """
    Função que auxilia a contagem das linhas ou das palavras consoante a flagC
    Args:
        lista (List): ocorrencias
        linhasPorFicheiro (int): linhas que cada ficheiro tem 
        palavras: palavras a procurar
        flagC: se a opção -c está ou não ativa
    Returns:
        Ocorrências por ficheiro bem como o tempo de processamento de cada um
        
    """
    ocorrenciasSemLinhas = list(map(lambda tuplo: tuplo[0], lista))
    ocorrenciasPorFicheiro = []
    for linhas in linhasPorFicheiro:
        ocorrenciasPorFicheiro.append(ocorrenciasSemLinhas[:linhas])
        ocorrenciasSemLinhas = ocorrenciasSemLinhas[linhas:]

    if (flagC == "ATIVA"):
        ocorrenciasPorFicheiroTotais = []
        for ficheiro in ocorrenciasPorFicheiro:
            ocorrenciasPorFicheiroTotais.append(list(functools.reduce(lambda x,y: x+y, ficheiro, [])))
        tempoInicio = time.time()
        resultado = []
        aux = []
        i = 0
        j = 0
        listaTempos = []
        while i < len(ocorrenciasPorFicheiroTotais) and j < len(palavras):
            
            aux.append(ocorrenciasPorFicheiroTotais[i].count(palavras[j]))
            j += 1
            if j == len(palavras):
                resultado.append(aux)
                listaTempos.append(time.time() - tempoInicio)
                aux = []
                i += 1
                j = 0
    else:
        ocorrenciasPorFicheiroFiltradas = []
        for ficheiro in ocorrenciasPorFicheiro:
            ocorrenciasPorFicheiroFiltradas.append(list(filter(lambda linha: len(linha) > 0, map(lambda linha: list(set(linha)), ficheiro))))
        
        ficheirosReduzidos = []
        for ficheiro in ocorrenciasPorFicheiroFiltradas:
            if ficheiro != []:
                ficheirosReduzidos.append(list(functools.reduce(lambda x,y: x+y, ficheiro, [])))
            else:
                ficheirosReduzidos.append([])

        resultado = []
        aux = []
        i = 0
        j = 0
        tempoInicio = time.time()
        listaTempos = []
        
        while i < len(ficheirosReduzidos) and j < len(palavras):
            aux.append(ficheirosReduzidos[i].count(palavras[j]))
            j += 1
            if j == len(palavras):
                resultado.append(aux)
                listaTempos.append(time.time() - tempoInicio)
                aux = []
                i += 1
                j = 0

    resultadoFinal = [resultado, listaTempos]
    return resultadoFinal
   

###################################################################################################################

def procuraPalavras(listaPalavras, listaFicheiros, flagA, flagC):
    """
    Função que faz a busca das palavras consoante as flags ativas
    Args:
        listaPalavras (List): lista de palavras a procurar
        listaFicheiros (List): lista com as linhas que o processo atual tem de processar
        flagA: se a opção -a está ou não ativa
        flagC: se a opção -c está ou não ativa
    """
    global sinal_terminar
    signal.signal(signal.SIGINT, terminaFilho)

    ocorrencias = []
    regex = constroiRegex(listaPalavras)

    linhasPorFicheiro = []
    for i in listaFicheiros:
        linhasPorFicheiro.append(len(i))
        if sinal_terminar:
            break 


    i = 0
    for ficheiro in listaFicheiros:
        for linha in ficheiro:
            ocorrencias.append((re.findall(regex, linha), linha))
            linhasProcessadas.value += 1
            if sinal_terminar:
                print("ultima linha que li:", linha)
                break  # se o pai pediu para terminar, termina nesta linha
            


    mutex.acquire()
    lista = pipe_filho.recv()

    if flagA == "ATIVA": # Proura as três palavras numa só
        resultadoOcorrencias = list(map(lambda tuplo: (list(set(tuplo[0])), tuplo[1]) , ocorrencias))
        result = list(filter(lambda linha: linha[0] != [] and len(linha[0]) == len(listaPalavras), resultadoOcorrencias))
        contadorDeLinhas.value += len(result)


    if flagA == "NAO_ATIVA": # Procura unicamente uma palavra em cada linha
        resultadoOcorrencias = list(map(lambda tuplo: (list(set(tuplo[0])), tuplo[1]) , ocorrencias))
        result = list(filter(lambda linha: linha[0] != [] and len(linha[0]) == 1, resultadoOcorrencias))
        contadorDeLinhas.value += len(result)


    if flagC == "ATIVA":
        listaContadores = (str(os.getpid()),auxDeContagem(ocorrencias, linhasPorFicheiro, listaPalavras, "ATIVA"))
        contadorDeOcorrencias.value += sum(functools.reduce(lambda x,y: x + y, listaContadores[1][0], []))
    
    if flagC == "NAO_ATIVA":
        listaContadores = (str(os.getpid()),auxDeContagem(ocorrencias, linhasPorFicheiro, listaPalavras, "NAO_ATIVA"))
        contadorDeOcorrencias.value += sum(functools.reduce(lambda x,y: x + y, listaContadores[1][0], []))

    lista += listaContadores
    pipe_filho.send(lista)

    time.sleep(1)

    imprime(result)

    mutex.release()


###################################################################################################################

def procuraPalavrasPai(listaPalavras, listaFicheiros, flagA, flagC):
    """
    Funçaõ que faz a busca das palavras consoante as flags ativas caso não seja designado nenhum processo filho
    Args:
        listaPalavras (List): lista de palavras a procurar
        listaFicheiros (List): lista com as linhas que o processo pai tem de processar
        flagA: se a opção -a está ou não ativa
        flagC: se a opção -c está ou não ativa
    Returns:
        Contador de linhas, ocorrências e o numero de ocorrencias por ficheiro

    """

    global sinal_terminar
    signal.signal(signal.SIGINT, terminaFilho)

    tempoInicio = time.time()

    ocorrencias = []
    regex = constroiRegex(listaPalavras)

    ficheirosLidos = [leFicheiro(ficheiro) for ficheiro in listaFicheiros]
    ficheirosFiltrados = [list(filter(lambda linha: linha != "", ficheiro)) for ficheiro in ficheirosLidos]

    linhasPorFicheiro = []
    for i in ficheirosFiltrados:
        linhasPorFicheiro.append(len(i))


    for ficheiro in ficheirosFiltrados:
        for linha in ficheiro:
            ocorrencias.append((re.findall(regex, linha), linha))


    if flagA == "ATIVA": # Proura as três palavras numa só
        resultadoOcorrencias = list(map(lambda tuplo: (list(set(tuplo[0])), tuplo[1]) , ocorrencias))
        result = list(filter(lambda linha: linha[0] != [] and len(linha[0]) == len(listaPalavras), resultadoOcorrencias))


    if flagA == "NAO_ATIVA": # Procura unicamente uma palavra em cada linha
        resultadoOcorrencias = list(map(lambda tuplo: (list(set(tuplo[0])), tuplo[1]) , ocorrencias))
        result = list(filter(lambda linha: linha[0] != [] and len(linha[0]) == 1, resultadoOcorrencias))

    contadorDeLinhas = len(result)

    if flagC == "ATIVA":
        tempoFim = time.time()
        tempoProcessamento = tempoFim - tempoInicio
        listaContadores = (str(os.getpid()), auxDeContagem(ocorrencias, linhasPorFicheiro, listaPalavras, "ATIVA"), tempoProcessamento)
        contadorDeOcorrencias = sum(functools.reduce(lambda x,y: x + y, listaContadores[1][0], []))

    if flagC == "NAO_ATIVA":
        tempoFim = time.time()
        tempoProcessamento = tempoFim - tempoInicio
        listaContadores = (str(os.getpid()), auxDeContagem(ocorrencias, linhasPorFicheiro, listaPalavras, "NAO_ATIVA"), tempoProcessamento)
        contadorDeOcorrencias = sum(functools.reduce(lambda x,y: x + y, listaContadores[1][0], []))

    imprime(result)

    return (contadorDeOcorrencias, listaContadores, contadorDeLinhas)

##################################################################################################################

def imprime(res):
    """
    Função que imprime o resultado das ocorrencias
    Args:
       res(list): Lista de tuplos que contém o resultado das ocorrências
    """
    for l in res:
        print(l[1])

###################################################################################################################

def criaProcessos(nFilhos, funcao, listaPalavras, listaFicheiros, flagA, flagC):
    """
    Função que cria processos filhos

    Args:
        nFilhos (int): número de processos a criar
        funcao: Função alvo do processo
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    listaProcessos = []
    lista = []

    global estadoProcesso
    global xP

    xP = nP[0] # número de processos
    sP = 0 

    l = []  
    for i in range(nFilhos):
        listaProcessos.append(Process(target = funcao, args = (listaPalavras, listaFicheiros[i], flagA, flagC, )))
        listaProcessos[i].start()
        pipe_pai.send(lista)


        if sP <= xP:
            estadoProcesso.append(l)
            estadoProcesso[sP].append(listaFicheiros[i])
            sP +=1

    signal.signal(signal.SIGINT, signal.SIG_IGN)


    for i in range(nFilhos):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        lista = pipe_pai.recv()

        listaOcorrencias.append(lista) 

        listaProcessos[i].join()
        

###################################################################################################################

def recebeComandos():
    """
    Função que lê a command line e regista os dados da mesma chamando a função principal
    """
    palavras = arguments.palavras
    ficheiros = arguments.f
    comandos = re.findall("-\w+", str(sys.argv))
    nProcessos = arguments.p
    tempo = arguments.w
    ficheiroSaida = arguments.o 

    global listaDeFicheiros
    listaDeFicheiros = ficheiros
    global tempoAlarmes

    if tempo != None: 
        tempoAlarmes = tempo[0]
    else:   
        tempoAlarmes = 0

    if tempo != None:
        signal.signal(signal.SIGALRM, sinal)
        signal.setitimer(signal.ITIMER_REAL, tempo[0], tempo[0])

    if len(palavras) > 3:
        print("Não pode procurar mais de 3 palavras de uma vez")
    elif "-c" in comandos and "-l" in comandos:
        print("Não pode usar ambos os comandos -c e -l em simultâneo")
    else:
        pgrepwc (palavras, ficheiros, comandos, nProcessos, ficheiroSaida)


###################################################################################################################
# FUNÇÃO PRINCIPAL                                                                                                #
###################################################################################################################



def pgrepwc (listaPalavras, listaFicheiros, listaOpcoes, nProcessos, ficheiroSaida):
    """
    Função que verifica quais as opções que foram passadas no comando, cria os processos para as opções, chama 
    a função que procura as palavras passadas no comando escreve o ficheiro binário para a respetiva opção.
    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
        listaOpcoes (List): Lista com os comandos utilizados
        nProcessos (int): Número de processos a serem criados
        ficheiroSaida (file.bin): Ficheiro binário
    """
    
    global nP
    nP = nProcessos

    if ("-p" in listaOpcoes):

        novaListaFicheiros = particaoJusta(listaFicheiros, nProcessos[0])

        if "-a" in listaOpcoes:
            if "-c" in listaOpcoes:
                criaProcessos(nProcessos[0], procuraPalavras, listaPalavras, novaListaFicheiros, "ATIVA", "ATIVA")
            if "-l" in listaOpcoes:
                criaProcessos(nProcessos[0], procuraPalavras, listaPalavras, novaListaFicheiros, "ATIVA", "NAO_ATIVA")
        else:
            if "-c" in listaOpcoes:
                criaProcessos(nProcessos[0], procuraPalavras, listaPalavras, novaListaFicheiros, "NAO_ATIVA", "ATIVA")
            if "-l" in listaOpcoes:
                criaProcessos(nProcessos[0], procuraPalavras, listaPalavras, novaListaFicheiros, "NAO_ATIVA", "NAO_ATIVA")

        if "-l" in listaOpcoes:
            print("A pesquisa resultou em: " + str(contadorDeLinhas.value) + " linhas")
        if "-c" in listaOpcoes:
            print("A pesquisa resultou em: " + str(contadorDeOcorrencias.value) + " ocorrências das palavras")

        if "-o" in listaOpcoes:
            
            ficheiroSaida = arguments.o[0]
            inicioExecucao = dataInicial
            duracaoExecucao = time.time() - inicio
            nFilhos = nProcessos[0]
            opcaoA = ""
            if "-a" in listaOpcoes:
                opcaoA = "ATIVA"
            else:
                opcaoA = "NAO ATIVA"

            opcaoC = ""
            if "-c" in listaOpcoes:
                opcaoC = "ATIVA"
            else:
                opcaoC = "NAO ATIVA"
        
            freqAlarmes = tempoAlarmes
            pidOcorrenciasLinhas = listaOcorrencias
            nomeFicheiros = listaDeFicheiros
            dim = distribuicaoDosFicheiros(listaDeFicheiros, nFilhos)
            palavras = listaPalavras
          
            dados = [inicioExecucao, duracaoExecucao, nFilhos, opcaoA, freqAlarmes, pidOcorrenciasLinhas, nomeFicheiros, dim, palavras, opcaoC]
            
            escreveParaBin(ficheiroSaida, dados)

    else:

        if "-a" in listaOpcoes: 
            if "-c" in listaOpcoes:
                res = procuraPalavrasPai(listaPalavras, listaFicheiros, "ATIVA", "ATIVA")
            if "-l" in listaOpcoes:
                res = procuraPalavrasPai(listaPalavras, listaFicheiros, "ATIVA", "NAO_ATIVA")
        else:
            if "-c" in listaOpcoes:
                res = procuraPalavrasPai(listaPalavras, listaFicheiros, "NAO_ATIVA", "ATIVA")
            if "-l" in listaOpcoes:
                res = procuraPalavrasPai(listaPalavras, listaFicheiros, "NAO_ATIVA", "NAO_ATIVA")
        
        if "-l" in listaOpcoes:
            print("A pesquisa resultou em: " + str(res[2]) + " linhas")
        if "-c" in listaOpcoes:
            print("A pesquisa resultou em: " + str(res[0]) + " ocorrências das palavras")
    

        if "-o" in listaOpcoes:
            ficheiroSaida = arguments.o[0]
            inicioExecucao = dataInicial
            duracaoExecucao = time.time() - inicio
            nFilhos = 0
            opcaoA = ""
            if "-a" in listaOpcoes:
                opcaoA = "ATIVA"
            else:
                opcaoA = "NAO ATIVA"

            opcaoC = ""
            if "-c" in listaOpcoes:
                opcaoC = "ATIVA"
            else:
                opcaoC = "NAO ATIVA"
            
            freqAlarmes = tempoAlarmes
            pidOcorrenciasLinhas = [res[1]]
            nomeFicheiros = listaDeFicheiros
            dim = distribuicaoDosFicheiros(listaDeFicheiros, nFilhos)
            palavras = listaPalavras

            dados = [inicioExecucao, duracaoExecucao, nFilhos, opcaoA, freqAlarmes, pidOcorrenciasLinhas, nomeFicheiros, dim, palavras, opcaoC]
            
            escreveParaBin(ficheiroSaida, dados)



###################################################################################################################

def sinal(sig, NULL):
    """
    Função que recebe o SIGALRM e que imprime o estado da execução periodicamente, com o número de ocorrências 
    e de linhas das palavras, os ficheiros que já foram ou estão a ser processados e o tempo decorrido desde o 
    início da execução do programa em micro-segundos.
    Args:
        sig (sinal): Signal handler
        NULL (frame)
    """

    fim = time.time()

    print("O número de ocorrências das palavras é: " + str(contadorDeOcorrencias.value))

    print("O número de linhas das palavras é: " + str(contadorDeLinhas.value))
    
    processamento = processamentoFicheiros(listaDeFicheiros)

    print("Os ficheiros que já foram processados são: " + str(processamento[0]))
    print("Os ficheiros que estão a ser processados são: " + str(processamento[1]))
    print("Decorreram: " + str(round(((fim-inicio)*1000000), 2)) + " micro-segundos")


###################################################################################################################

def processamentoFicheiros(listaFicheiros):
    """
    Função que vê quais ficheiros já foram processados e quais estão em processamento
    Args:
        listaFicheiros (List): Lista de ficheiros
    Returns:
        Tuplo com ficheiros processados e ficheiros não processados
    """
    ficheirosLidos = [[ficheiro ,leFicheiro(ficheiro)] for ficheiro in listaFicheiros]
    listaDeLinhas = [[ficheiro[0],len(ficheiro[1])] for ficheiro in ficheirosLidos]
    ficheirosProcessados = processados(listaDeLinhas)
    ficheirosNaoProcessados = listaFicheiros[len(ficheirosProcessados):]
    return (ficheirosProcessados,ficheirosNaoProcessados)


###################################################################################################################

def processados(ficheiros): 
    """
    Função que verifica quais foram os ficheiros processados
    Args:
        ficheiros (List): Lista de ficheiros
    Returns:
        Ficheiros processados
    """
    ficheirosProcessados = []
    l_processadas = linhasProcessadas.value

    i = 0
    while l_processadas > 0:
        
        if (l_processadas - ficheiros[i][1]) > 0:
            ficheirosProcessados.append(ficheiros[i][0])
            l_processadas -= ficheiros[i][1]
            i += 1
        
        if (l_processadas - ficheiros[i][1]) == 0:
            ficheirosProcessados.append(ficheiros[i][0])
            l_processadas = 0
        
        if (l_processadas - ficheiros[i][1]) < 0:
            l_processadas = 0
    
    return ficheirosProcessados

###################################################################################################################    

def experiencia(listaProcessos, listaFicheiros):
    """
    Função que auxilia a distribuição dos ficheiros pelos processos
    Args:
        listaProcessos (List): lista de processos
        listaFicheiros (List): lista de ficheiros
    Returns:
        Os ficheiros que cada processo vai processar
    """

    i = 0
    j = 0
    res = []
    final = []

    
    while i < len(listaProcessos) and j < len(listaFicheiros):
        if (listaProcessos[i] - listaFicheiros[j][1]) < 0:
            res += [(listaFicheiros[j][0], listaProcessos[i])]
            listaFicheiros[j][1] -= listaProcessos[i]
            listaProcessos[i] = 0

        if (listaProcessos[i] - listaFicheiros[j][1]) > 0:
            listaProcessos[i]-= listaFicheiros[j][1]
            res += [(listaFicheiros[j][0], listaFicheiros[j][1])]
            listaFicheiros[j][1] = 0

        if (listaProcessos[i] - listaFicheiros[j][1]) == 0:
            res += [(listaFicheiros[j][0], listaFicheiros[j][1])]
            listaProcessos[i] = 0
            listaFicheiros[j][1] = 0

        if listaProcessos[i] == 0:
            i+=1
            final.append(res)
            res = []
        
        if listaFicheiros[j][1] == 0:
            j += 1

    return final

###################################################################################################################

def distribuicaoDosFicheiros(listaFicheiros, nProcessos):
    """
    Função que trata da distribuição de ficheiros para x processos
    Args:
        listaFicheiros (List): lista de ficheiros
        nProcessos (int): numero de processos
    Returns: 
        Os ficheiros que cada processo vai processar
    """

    ficheirosLidos = [[ficheiro ,leFicheiro(ficheiro)] for ficheiro in listaFicheiros]
    ficheirosFiltrados = [[ficheiro[0],list(filter(lambda linha: linha != "", ficheiro[1]))] for ficheiro in ficheirosLidos] 
    listaDeLinhas = [[ficheiro[0],len(ficheiro[1])] for ficheiro in ficheirosFiltrados]
    
    numeroTotalDeLinhas = sum(map(lambda f: f[1], listaDeLinhas))

    if nProcessos == 0:
        nProcessos = 1

    linhasPorProcesso = numeroTotalDeLinhas//nProcessos
    sobra = numeroTotalDeLinhas % nProcessos

    lista = []
    for i in range(nProcessos):
        lista.append(linhasPorProcesso)

    lista[-1] += sobra 

    return experiencia(lista, listaDeLinhas)

###################################################################################################################

if __name__ == '__main__':

    parser = argparse.ArgumentParser() 

    # Adiciona argumentos ao parser
    parser.add_argument('funcao', help="Define qual a função a ser executada")
    parser.add_argument('-a', help="Define se o resultado são as linhas de texto que contêm unicamente uma das palavras ou todas as palavras." +
                                    " Por omissão, somente as linhas contendo unicamente uma das palavras serão devolvidas", action='store_true') 
    parser.add_argument('-c', help="Permite obter o número de ocorrências encontradas das palavras a pesquisar", action='store_true') 
    parser.add_argument('-l', help="Permite obter o número de linhas devolvidas da pesquisa", action='store_true') 
    parser.add_argument('-p', help="permite definir o nível de paralelização do comando", type=int, nargs=1) 
    parser.add_argument('-w', help="permite definir o periodo que se vai enviar um sinal", type=int, nargs=1) 
    parser.add_argument('-o', help="permite definir o ficheiro de output", type=str, nargs=1) 
    parser.add_argument('palavras', help="É preciso dar um comando", type=str, nargs='+') #Limitar a 3 palavras
    parser.add_argument('-f', help="É preciso dar um comando", type=str, nargs='+')

    arguments = parser.parse_args()
    
    if sys.argv[1] == "pgrepwc":

        recebeComandos()
