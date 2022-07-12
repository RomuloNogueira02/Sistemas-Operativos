###################################################################################################################
# LISTA DE IMPORTS                                                                                                #
###################################################################################################################
import sys, argparse
import pickle 
import datetime

"""
Função que lê o histórico de execução do programa pgrepwc
Args:
    ficheiro(str): nome do ficheiro que se pretende ler e imprimir
"""
def hpgrepwc(ficheiro):
    with open(ficheiro,"rb") as inFile:
        dados = pickle.load(inFile)

        print("Início da execução da pesquisa: " + str(dados[0]))
        print("Duração da execução: " + str(datetime.timedelta(seconds=dados[1])))
        print("Número de processos filhos: " + str(dados[2]))
        if len(dados[5]) > 1:
            dados[5] = sorted(dados[5])
        if (dados[3] == 'ATIVA'):
            print("Opção -a ativada: Sim" )
        else:
            print("Opção -a ativada: Não" )
        print("Emissão de alarmes no intervalo de " + str(dados[4]) + " segundos")

        i = 0
        for processo in dados[5]:
            i += 1
            print("Processo: " + str(processo[0]))
            h = 0
            for tuplo in dados[7][i-1]:

                print("       ficheiro: " + tuplo[0])
                print("              tempo de pesquisa: " + str(datetime.timedelta(seconds=processo[1][1][h])))
                print("              dimensão do ficheiro: " + str(tuplo[1]))
              
                j = 0
                for palavra in dados[8]:
                    
                    if (dados[9] == "ATIVA"):
                        print("              número de ocorrências da palavra " + '"' + palavra + '"' + ": " + str(processo[1][0][h][j]))
                    else:
                        print("              número de linhas da palavra " + '"' + palavra + '"' + ": "+ str(processo[1][0][h][j]))
                    j += 1
                h += 1

if __name__ == '__main__':

    parser = argparse.ArgumentParser() 

    # Adiciona argumentos ao parser
    parser.add_argument('funcao', help="Define qual a função a ser executada")
    parser.add_argument('file', help="É preciso dar um comando", type=str, nargs=1) 

    arguments = parser.parse_args()
    
    if sys.argv[1] == "hpgrepwc":
        
        hpgrepwc(sys.argv[2])
