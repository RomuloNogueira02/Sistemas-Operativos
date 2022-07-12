###################################################################################################################
# LISTA DE IMPORTS                                                                                                #
###################################################################################################################
import sys, os, argparse
import re, unicodedata
from multiprocessing import Process, Value

###################################################################################################################
# Definição das variáveis                                                                                          #
###################################################################################################################

contadorDeOcorrencias = Value("i", 0)
contadorDeLinhas = Value("i", 0)

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
    contadorLinhas = 1
    resultado = []
    with open(ficheiro, 'r', encoding='utf8') as ficheiroTexto:
        for linha in ficheiroTexto:
            resultado.append((contadorLinhas,linha)) 
            contadorLinhas += 1
    resultado = list(map(lambda tuplo: (tuplo[0],tuplo[1].strip('\n')), resultado))       

    return resultado

###################################################################################################################
def procuraPalavras(palavra, ficheiro):
    """
    Função que procura UMA palavra em UM ficheiro  

    Args:
        palavra (String): Palavra a procurar    
        ficheiro (String): Ficheiro onde procurar a palavra

    Returns:
        List: lista de tuplos em que cada tuplo tem a forma: 
        (palavra encontrada, linha em que foi encontrada)
    """
    ficheiroLido = leFicheiro(ficheiro)
    regex = r"\b" + re.escape(transformaPalavra(palavra)) + r"\b"
    
    ocorrencias = []

    for tuplo in ficheiroLido:
        ocorrencias.append(
            (re.findall(regex, unicodedata.normalize("NFD", tuplo[1]).encode("ascii","ignore").decode("utf-8"), 
            flags= re.IGNORECASE), tuplo[1]))

    resultadoOcorrencias = list(filter(lambda linha: linha[0] != [], ocorrencias))

    return resultadoOcorrencias 

###################################################################################################################
# Função usada com o comando -l
def numLinhasOcorre (palavra, ficheiro): 
    """
    Função que verifica o número de linhas em que UMA palavra aparece em UM ficheiro

    Args:
        palavra (String): palavra a procurar
        ficheiro (String): Ficheiro onde procurar a palavra

    Returns:
        int: Número de linhas em que a palavra existe
    """
    return len(procuraPalavras(palavra, ficheiro)) 

###################################################################################################################
# Função usada com o comando -c
def contadorOcorrencias (palavra, ficheiro):
    """
    Função que conta o número de ocorrências de UMA palavra em UM ficheiro

    Args:
        palavra (String): Palavra a procurar
        ficheiro (String): Ficheiro onde procurar a palavra

    Returns:
        int: Número de ocorrências da palavra no ficheiro
    """
    listaOcorrencias = list(map(lambda tuplo: tuplo[0], procuraPalavras(palavra,ficheiro)))
    return sum(map(lambda linha: len(linha), listaOcorrencias)) 

###################################################################################################################
def transformaPalavra(palavra):
    """
    Função que tranforma uma palavra colocando-a toda em minúsculas e sem acentos

    Args:
        palavra (String): Palavra a transformar

    Returns:
        String: Palavra transformada
    """
    return unicodedata.normalize("NFD", palavra).encode("ascii","ignore").decode("utf-8").lower()

###################################################################################################################
def verificacao (listaPalavras, tuplo):
    """
    Função que verifica se um conjunto de palavras está presente numa lista

    Args:
        listaPalavras (List): lista de palavras a procurar
        tuplo (Tuple): tuplo que contém as lista de palavras e string ([listaPalavras], string da sua ocorrência)

    Returns:
        boolean: Se as palavras estão ou não na lista
    """
    var = True
    dadosAVerificar = list(map(lambda palavra: transformaPalavra(palavra) ,tuplo[0]))
    palavrasAVerificar = list(map(lambda palavra:transformaPalavra(palavra) ,listaPalavras))
    for palavra in palavrasAVerificar:
        if palavra not in dadosAVerificar:
            var = False
    return var

###################################################################################################################
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
        regex = regex + transformaPalavra(listaPalavras[i]) + "|" 
    
    return r"\b(" + regex + transformaPalavra(listaPalavras[-1]) + r")\b"

###################################################################################################################
def parteLista (lista, n):
    """
    Função que a partir de uma lista de palavras cria uma nova partida em n partes cada uma contendo palavras 
    da lista original. Se o n for maior que o len(lista) a lista divide-se à mesma em n partes

    Args:
        lista (List): Lista de palavras
        n (int): número inteiro

    Returns:
        List: lista de n listas do tipo: [['palavra1', 'palavra4'], ['palavra2'], ['palavr3']] *para n=3
    """
    listaFinal = []
    
    for i in range(len(lista)):
        if i < n:
            listaFinal.append([lista[i]])

        else:
            novoIndice = i - n
            while novoIndice > n - 1:
                novoIndice -= n   
            listaFinal[novoIndice].append(lista[i])
    return listaFinal

###################################################################################################################
def criaProcessos(nFilhos, funcao, listaPalavras, listaFicheiros):
    """
    Função que cria processos filhos

    Args:
        nFilhos (int): número de processos a criar
        funcao (?): Função alvo do processo
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    listaProcessos = []

    for i in range(nFilhos):
        listaProcessos.append(Process(target = funcao, args = (listaPalavras, listaFicheiros[i], )))
        listaProcessos[i].start()

    for i in range(nFilhos):
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

    if len(palavras) > 3:
        print("Não pode procurar mais de 3 palavras de uma vez")
    elif "-c" in comandos and "-l" in comandos:
        print("Não pode usar ambos os comandos -c e -l em simultâneo")
    else:
        pgrepwc (palavras, ficheiros, comandos, nProcessos)

###################################################################################################################
# OPÇÃO -a                                                                                                        #
###################################################################################################################
def opcaoA (listaPalavras, listaFicheiros):
    """
    Função que retorna as linhas de texto que contêm as palavras passadas na listaPalavras

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros

    Returns:
        List: Lista de tuplos do tipo: [(['palavra1], 'linha onde ocorre a palavra')]
    """
    ocorrencias = []
    ficheirosLidos = [leFicheiro(ficheiro) for ficheiro in listaFicheiros]
    regex = constroiRegex(listaPalavras)
    
    for linha in ficheirosLidos:
        for tuplo in linha:
            ocorrencias.append((re.findall(regex, 
                unicodedata.normalize("NFD", tuplo[1]).encode("ascii","ignore").decode("utf-8"), 
                flags= re.IGNORECASE), tuplo[1]))
    
    resultadoOcorrencias = list(filter(lambda linha: linha[0] != [], ocorrencias))
 
    return list(filter(lambda tuplo: verificacao(listaPalavras,tuplo), resultadoOcorrencias)) 

###################################################################################################################
def opcaoAtodasPalavras(listaPalavras, listaFicheiros):
    """
    Função que imprime as linhas onde ocorrem todas as palavras desejadas (não imprime se a linha só tiver uma delas)

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    for tuplo in opcaoA(listaPalavras, listaFicheiros):
        print(tuplo[1])

###################################################################################################################
def opcaoAumaPalavra(listaPalavras, listaFicheiros):
    """
    Função que imprime as linhas que contêm apenas uma das palavras pedidas

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    listaDasLinhas = [] 

    for palavra in listaPalavras:
        for ficheiro in listaFicheiros:
            listaDasLinhas.append(list(map(lambda tuplo: tuplo[1], procuraPalavras(palavra, ficheiro))))
  
    for lista in listaDasLinhas:
        for linha in lista:
            print(linha)

###################################################################################################################
# OPÇÃO -l -> Contador de linhas                                                                                  #
###################################################################################################################
def opcaoLsemA (listaPalavras, listaFicheiros):
    """
    Função que obtém o número de linhas devolvidas da pesquisa por palavra

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    numLinhasPorPalavra = []

    for palavra in listaPalavras:
        for ficheiro in listaFicheiros:
            numLinhasPorPalavra.append((palavra, numLinhasOcorre(palavra, ficheiro)))

    contadorDeLinhas.value += sum(map(lambda tuplo: tuplo[1], numLinhasPorPalavra))
    
    opcaoAumaPalavra(listaPalavras, listaFicheiros) 

###################################################################################################################
def opcaoLcomA(listaPalavras, listaFicheiros):
    """
    Função que obtém o número de linhas devolvidas da pesquisa de todas as palavras

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    numLinhasPorPalavra = opcaoA(listaPalavras, listaFicheiros)
    listaFinal = []
   
    for tuplo in numLinhasPorPalavra:
        listaFinal.append(tuplo[1])

    contadorDeLinhas.value += len(listaFinal)

    opcaoAtodasPalavras(listaPalavras, listaFicheiros)

###################################################################################################################
# OPÇÃO -c -> Contador de ocorrências                                                                             #
###################################################################################################################
def opcaoCcomA(listaPalavras,listaFicheiros):
    """
    Função que obtém o número de ocorrencias das palavras indicadas nas linhas onde ambas as palavras aparecem 

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    ocorrenciasPorPalavra = []

    for palavra in listaPalavras:
        for ficheiro in listaFicheiros:
            ocorrenciasPorPalavra.append((palavra, contadorOcorrencias(palavra,ficheiro)))

    contadorDeOcorrencias.value += sum(map(lambda tuplo : tuplo[1], ocorrenciasPorPalavra))

    opcaoAtodasPalavras(listaPalavras, listaFicheiros)

###################################################################################################################
def opcaoCsemA(listaPalavras,listaFicheiros):
    """
    Função que obtém o número de ocorrencias das palavras indicadas nas linhas onde pelo menos uma das palavras aparece

    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
    """
    ocorrenciasPorPalavra = []
    for palavra in listaPalavras:
        for ficheiro in listaFicheiros:
            ocorrenciasPorPalavra.append((palavra, contadorOcorrencias(palavra,ficheiro)))

    contadorDeOcorrencias.value += sum(map(lambda tuplo : tuplo[1], ocorrenciasPorPalavra ))
    opcaoAumaPalavra(listaPalavras, listaFicheiros)

###################################################################################################################
# FUNÇÃO PRINCIPAL                                                                                                #
###################################################################################################################
def pgrepwc (listaPalavras, listaFicheiros, listaOpcoes, nProcessos):
    """
    Função que ...
    Args:
        listaPalavras (List): Lista de palavras
        listaFicheiro (List): Lista de ficheiros
        listaOpcoes (List): Lista com os comandos utilizados
        nProcessos (int): Número de processos a serem criados
    """
    if ("-p" in listaOpcoes):
        
        novaListaFicheiros = list(map(lambda ficheiro: [ficheiro], listaFicheiros))

        nFilhos = nProcessos[0]
        
        nFicheiros = len(listaFicheiros)
        if nFilhos > nFicheiros:
            nFilhos = nFicheiros
        
        if nFilhos < nFicheiros:
            novaListaFicheiros = parteLista(listaFicheiros, nFilhos)

        if "-l" in listaOpcoes:

            if "-a" not in listaOpcoes: 
                criaProcessos(nFilhos, opcaoLsemA, listaPalavras, novaListaFicheiros)
            
            else:
                criaProcessos(nFilhos, opcaoLcomA, listaPalavras, novaListaFicheiros)

            print("A pesquisa resultou em: " + str(contadorDeLinhas.value) + " linhas") 

        elif "-c" in listaOpcoes:

            if "-a" not in listaOpcoes:
                criaProcessos(nFilhos, opcaoCsemA, listaPalavras, novaListaFicheiros)
            
            else: 
                criaProcessos(nFilhos, opcaoCcomA, listaPalavras, novaListaFicheiros)

            print("A pesquisa resultou em: " + str(contadorDeOcorrencias.value) + " ocorrências das palavras")
             
    else:
        if "-l" in listaOpcoes:

            if "-a" not in listaOpcoes: #o número de linhas devolvido é por palavra
                opcaoLsemA(listaPalavras, listaFicheiros)

            else:
                opcaoLcomA(listaPalavras, listaFicheiros)
            
            print("A pesquisa resultou em: " + str(contadorDeLinhas.value) + " linhas")

        
        elif "-c" in listaOpcoes:

            if "-a" not in listaOpcoes: #o número de linhas devolvido é por palavra
                opcaoCsemA(listaPalavras,listaFicheiros)

            else:
                opcaoCcomA(listaPalavras,listaFicheiros)

            print("A pesquisa resultou em: " + str(contadorDeOcorrencias.value) + " ocorrências das palavras")

###################################################################################################################
# VER SE NÃO TEM DE SER CORRIGIDA
if __name__ == '__main__':

    parser = argparse.ArgumentParser() 

    # Adiciona argumentos ao parser
    parser.add_argument('funcao', help="Define qual a função a ser executada")
    parser.add_argument('-a', help="Define se o resultado são as linhas de texto que contêm unicamente uma das palavras ou todas as palavras." +
                                    " Por omissão, somente as linhas contendo unicamente uma das palavras serão devolvidas", action='store_true') 
    parser.add_argument('-c', help="Permite obter o número de ocorrências encontradas das palavras a pesquisar", action='store_true') 
    parser.add_argument('-l', help="Permite obter o número de linhas devolvidas da pesquisa", action='store_true') 
    parser.add_argument('-p', help="permite definir o nível de paralelização do comando", type=int, nargs=1) 
    parser.add_argument('palavras', help="É preciso dar um comando", type=str, nargs='+') #Limitar a 3 palavras
    parser.add_argument('-f', help="É preciso dar um comando", type=str, nargs='+')

    arguments = parser.parse_args()

    if sys.argv[1] == "pgrepwc":
        recebeComandos()