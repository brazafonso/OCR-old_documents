# Papers - estudo da arte

# OCR, historia e estado da arte:

## Optical character recognition (OCR) : https://dl.acm.org/doi/10.5555/1074100.1074664 - 2003

* poucas citações
* explicação do processo geral de OCR:
    * principalmente composto por 3 fases
        * analise de documento - extração/isolamento dos caracteres
        * reconhecimento dos caracteres
        * processamento contextual - ex.: fazer correçoes de acordo com conhecimentos lexicais de uma linguagem
    * explicação geral de algoritmo de reconhecimento de caracteres
        * feature extractor
            * template matching || feature matching || caracteristicas de pixeis
            * Redes neuronais
            * Modelos estatisticos
            * Funções discriminantes
        * classifier
    * problemas de OCR
        * problemas com o documento orginal
            * danos físicos
            * texto manuscrito ou com fontes que dificultam reconhecimento
        * problemas com o processo de digitalização
            * má iluminação
            * má resolução
        * conjunto dos caracteres reconhecidos
        * má discriminação do algoritmo de reconhecimento
    * online vs offline OCR

* distinção entre OCR e ICR
    * ICR é uma evolução de OCR para algoritmos capazes de se adaptar a características que OCR está limitado , ex.: fonte do texto~

* breve historia de OCR (desatualizada)
* OCR para tarefas especificas


## Optical character recognition: An overview and an insight : https://ieeexplore.ieee.org/document/6993174 - 2014

* online vs offline OCR:
    * reflete o tipo de input
    * online - on the go OCR, o texto é escrito e reconhecido antes de estar terminado
        * ex.: aplicações para smartphone, tablets digitalizadores
        * harware preparado para capturar dados de forma precisa
    * offline - OCR num texto completo
        * necessario pre-processamento devido a erros do input (imagens)

* maior problema da area continua a ser escrita à maior
* modelos ja sao capazes de reconhecer caracteres partidos ou destorcidos

* Primeiras tentativas de OCR foram motivadas para ajudar os os inibidos de ler - possibilitar um modo de transcrição automática do texto para um formato que depois podesse ser compreendido por eles (braile ou audio)
* Gerações de OCR
    * 1º Apenas reconhece certas fontes e caracteres 
    * 2º Reconhece para certos caracteres, escrita manual
    * 3º Maior capacidade para reconhecer escrita manual e lidar com pior qualidade de input
    * 4º Capacidade para lidar com documentos complexos, de linguagens diferentes, com ou sem cor e relativo dano
* Descrição breve, de forma cronológica, dos vários métodos manifestados até 2013, tanto para offline como online OCR e para escrita à mão e máquina. (grande parte para alfabetos asiaticos)
    * tecnicas de pre processamento
    * metodos de reconhecimento
    * classifiers
    * pos processamento


## Text extraction using OCR: A Systematic Review : https://ieeexplore.ieee.org/document/9183326/metrics#metrics - 2020

* breve introducao a OCR
* mençao de alguns motores de OCR, e que tesseract é o mais popular
    * imersão de sistemas online (serviços OCR)
* explicação dos principais passos de OCR
    * Aquisição de imagem
        * inclui quantetização e compressão pelo formato guardado
    * Pre processamento
        * tratamento de imagem para possibilitar melhores resultados
            * binarização
            * contrastar melhor as arestas, suavizar a imagem
            * remoção de reduzido
            * deteção e remoção de rotação
    * Segmentação
        * Segmentação da página para apenas manter texto para reconhecimento (repondo mais tarde)
        * Segmentação de caracteres
            * Normalização da imagem
            * Processamento morfológico
    * Extração de features (dos caracteres e palavras)
    * Classificação dos vetores
        * Apenas descritos classificadores usando ML
    * Pos processamento
        * Correção de erros ortograficos, etc.
* descrição de algumas técnicas novas com potencial
* áreas de pesquisa mais relevantes
    * documentos históricos
    * televisão
    * segurança ex.: matrículas

## An Overview of the Tesseract OCR Engine : https://ieeexplore.ieee.org/document/4376991 - 2007

* muito especifico sobre o funcionamento da tecnologia (utilidade questionavel quando apenas a quero usar e nao imitar)


# Formato de documentos:

## Comparison of JPEG's competitors for document images : https://ieeexplore.ieee.org/document/7367194 - 2015
* comparação entre diferentes formatos de imagem (todos lossy)
* conclusao que formato JPEG é o pior deles 




# OCR tratamento de imagem

## Image Preprocessing for Improving OCR Accuracy - https://ieeexplore.ieee.org/document/4283429 - 2007
* estudo focado para imagens tiradas por camaras moveis, ex.: telemovel
* focado para correções de orientação e distorção de imagem
* resumo de estudo anterior em que mostram que maiores problemas de imagem para OCR são problemas de ruido, orientação, baixa resolução e distorção de imagem
* usam ABBYY
* corrigir orientação
    * encontrar pixeis mais à esquerda
    * limpar de forma a criar uma linha continua na margem esquerda do texto
    * calcular angulo de rotacao necessario para corrigir
* corrigir disturção
    * feito de forma manual
    * desenhada curva com 4 pontos nós
    * de acordo com a variação dos nós na curva é calculado o quadrilatero da zona de disturcao
    * com a zona delimitada a correção é realizada
* conjunto de resultados para casos com disturção e rotação e com ou sem ruido
    * alguns filtros como mediana, minimo e ajuste de intensidade para tratamento do ruido sao mencionados


## Pre-Processing of Degraded Printed Documents by Non-local Means and Total Variation : https://ieeexplore.ieee.org/document/5277501/citations?tabFilter=papers#citations - 2009
* mençao de alguns outros filtros para redução de ruido como Markov Random Field
* apresentação de dois métodos para pre processamento focado na recuperação ao nivel das palavras e caracteres, diminuindo o ruido ao seu redor e tentanto aumentar o contraste
    * non-local means
        * uso dos valores dos pixeis vizinhos diretos e de uma caixa de vizinhança n direta para calcular medias
    * total variation minimization
        * usa modelos de imagens
* NLMeans teve muito melhor e mais consistente eficácia
* tamanho de dataset de teste nao muito claro
* usado tesseract para os testes
    * com e sem correções com dicionario (opcoes do tesseract)
* concluem que TV é melhor para documentos antigos, mas os proprios resultados raramente mostram isso


## DE-GAN: A Conditional Generative Adversarial Network for Document Enhancement - https://ieeexplore.ieee.org/document/9187695 - 2020
* focado numa proposta ML, mais especificamente GAN (generative adversarial network) condicional, para o pre processamento de imagens (ruido, disturcao, watermarks, binerizaçao)
* resumo de trabalho relacionado sobre pre processamento de documentos
    * binarização
        * processo de separação entre texto e degradação
        * maioriamente baseado em thresholding (limiarização)
        * resumo de diferentes metodos propostos e conclusao que estes sao muito dependentes do estado original do documento, nivel de thresholding, mesmo que adaptativo, pode estragar o documento
        * por este motivo, propoe que ML para tentar separar o texto do ruido tem melhor resultados (admitindo a necessidade de quantidades generosas de treino com bons datasets)
    * remoção de watermarks
        * normalmente um problema de processamento de imagens naturais
        * maioritariamente uma questao da area de ML
    * super-resolução
        * principalmente com uso de GANS
        * otimos resultados
        * alguns exemplos dados: pix2pix-HF, CycleGAN
* proposta
    * DE-GAN, uma cGAN
        * explicação de que GAN é composta por duas componentes principais
        * gerador, que aprende a transformação de ruido para imagem
        * discriminador, que aprende a distinção entre imagem do gerador e a original
        * as duas componentes competem uma com a outra para tentarem: o gerador enganar o discriminador; o discriminador perceber quando uma imagem foi gerada
        * esta adversidade propoe uma constante evolucao das duas redes
        * as GANS condicionais adicionam um fator, uma imagem imagem condicionada, para o gerador aprender em conjunto
    * Neste caso, alem da semelhança com a imagem esperada, eles têm o cuidado de na função de loss terem em conta se houve texto perdido (reconhecido), de modo a obrigar a diminuir a perda de legibilidade
* resultados aparentemente melhores do que todos as outras tecnologias
* top em competição de kaggle de remoção de ruido de documentos
* casos de teste impressionantes para tratamento de : watermark, ruido, imagem desfocada

## Enhancing OCR Accuracy with Super Resolution - https://ieeexplore.ieee.org/document/8545609 - 2018
* proposta usando GAN, focado em documentos com baixa resolução
* propõe que o metodo implementado dara melhor resultado do que os metodos comuns, ex.: interpolação, que normalmente resultam em imagens desfocadas.
* testes em imagens de resolução tao baixa como 75 dpi
* resumo do estado da arte
    * algoritmos manuais
        * resultam usualmente em imagens desfocadas
    * redes convulocionais
        * baixo resultado
        * necessita de muitos dados para treino
    * bons resultados apenas ate resoluções de 100 dpi
* nos testes, tesseract tem resultado muito baixo nas imagens de baixa resolução
* os resultados pretendem nao so aumentar a taxa de acerto em OCR, mas tambem a legibilidade por pessoas (melhorar tanto a imagem para leitura de um computador como para uma pessoa)



## Approach for Preprocessing in Offline Optical Character Recognition (OCR) - https://ieeexplore.ieee.org/document/9791698 - 2022
* resumo e enumeração das diferentes tecnicas de pre processamento que podem ser aplicadas para OCR
* melhoria de imagem
    * correção de inclinação (slant)
        * principal uso para texto manuscrito
        * varios metodos
            * calcular media de inclinação e corrigir de acordo
            * projecoes em histogramas para minimização ou maximização
            * estatisticas sobre os contornos das imagens
    * orientação/rotação
    * remoção de ruido
        * suavização
            * linear : geralmente usando a media dos vizinhos relevantes (cinzentos para cima) de cada pixel
            * não linear : mais capaz de lidar com desafios
                * min : minimo valor da vizinhança
                * max : maximo valor da vizinhança
                * mediana : valor central da vizinhança
            * adaptativo : varia o comportamento de acordo com as caracteristicas estatisticas de uma zona
    * filtro gaussiano
        * melhorias possiveis: reduz ruido, margens mais acentuadas, remoção de disturções visuais
    * NAS-RUIF
        * imagens desfocadas
* restauração de imagem
    * IBD (iterative blind de-convolution)
        * imagens desfocadas
        * processeco que procura arestas acentuadas para desfocar
        * processo que pode ser repetido iterativamente
* segmentação de imagem
    * segmentação em linhas utilizando histogramas de projeção horizontal
    * segmentação de palavras utilizando histogramas de projeção vertical (a partir dos resultados do passo anterior)
    * segmentação de letras
        * pode ou não ser feito devido à possibilidade de letras conectadas
* práticas comuns
    * binarização
        * de greyscale para black and white
            * thresholding global é melhor
        * cor para black and white
            * local thresholding é melhor
    * transformações morfológicas
        * dilatação : expandir os pixeis pretos
        * erosão: reduzir os pixeis pretos
        * thinning e skeletonization 
            * redução de grupos de pixeis (objetos) para terem 1 pixel de grossura
        * deteção de borda : descoberta de contornos (locais em que existe mudança abrupta da vizinhança)
* alguns resultados, mas sem comparação com sem pre-processamento (não da grande utilidade)



## Improved optical character recognition with deep neural network - https://ieeexplore.ieee.org/document/8368720 - 2018
* outro exemplo de ML para OCR
* processo total de OCR
* usam CNN e Transfer Learning
* rede de feature extraction e rede de classificador
* poucos dados de teste, resultados ok
* base para criar sistemas OCR com IA


## Selecting Automatically Pre-Processing Methods to Improve OCR Performances - https://ieeexplore.ieee.org/document/8269967 - 2017
* proposta - sistema que automaticamente escolhe os metodos e parametros destes mais apropriados para o pre processamento numa imagem
* resumo de metodos de pre processamento
    * binarização
    * reducao de ruido
    * aumento de contrastes
* testes das tecnicas
    * tesseract
    * LSTM OCR
    * avaliacao das diferentes tecnicas nos dois OCRs
        * prova que para casos diferentes, diferentes tecnicas vao resultar em melhor performance
        * em alguns casos, certos algoritmos pioram o reconhecimento de texto
        * LSTM muito mais consistente do que tesseract para as imagens de baixa qualidade
* proposta
    * CNN que devolve o conjunto de pre processamento ideal
        * 1 classe para cada combinação possivel de pre processamentos 
        * 21 classes no total
* resultados mostram grande aumento no acerto do Tesseract
    * tabela com metodos mais escolhidos
        * reducao de ruido + binarização Su & al (35%)
        * image sharpening Signh + binarização (34%)
        * binarização (23%)



# Identificação de imagens


# OCR Pos processamento

## Survey of Post-OCR Processing Approaches : https://dl.acm.org/doi/10.1145/3453476
* estudo extenso e compreensivo sobre a necessidade de pos processamento, as tecnicas comuns e a sua eficacia, e o caminho que a area esta a tomar
* pos processamento é essencial nao so para obter a informação de forma correta, mas também por questões de indexação dos proprios documentos
    * exposição sobre erros de OCR que foram calculados diminuir a taxa de acertos com termos de procura populares - Information Retrieval
    * para NLP, como análise de sentimentos, taxas de erro por volta dos 7% mostram que pode afetar a performance tanto como 30%.
* apresentação do problema de pos processamento de OCR
    * tendo uma sequencia de tokens s dados pelo OCR e uma sequencia de palavras w representantes da ground truth de um documento, tenta-se a aproximar o conjunto S ao conjunto W o maximo possivel
    * alguns erros detetaveis:
        * não palavra: caso s não pertença ao conjunto de palavras do dicionário (deteção automática)
        * palavra errada: caso sn seja diferente de wn (necessário ground truth e técnicas de alinhamento para detetar, ou modelos de previsão de texto)
    * no caso de deteção erros, na maior parte dos casos são propostos modelos probabilísticos que procuram entre as possíveis palavras tendo em conta a palavra errada
* técnicas de pos-OCR
    * manuais
        * principalmente para criação de dados de teste
        * voluntariado
        * jogos, projetos de correção de texto antigos, captcha
    * (semi-)automáticas
        * palavras isoladas
            * considera:
                * presença no dicionario
                * confiança do reconhecimento
                * frequencia de uso
                * similaridade com entradas conhecidas do léxico
            * maioritariamente para problemas de palavras não reais ou desconhecidas
            * técnicas
                * junção de Outputs de OCR
                    * 3 fases
                        * 1º obenção de varios resultados de OCR
                            * varios scannings do texto
                            * mudança de parametros de pre processamento antes de fazer varios scannings do texto
                            * varios scannings com Motores OCR diferentes
                        * 2º alinhamento de texto
                            * uso de grafos para alinhar palavras numa linha
                            * alinhamento hierarquico, pagina, linha, palavra
                        * 3º fase de decisão
                            * decidir qual dos inputs escolher
                            * votação, dicionário, Modelos de LSTM; são alguns exemplos de decisores
                    * limitado às palavras dos vários inputs, mas computação necessária
                * vias lexicais
                    * cálculos de similaridade entre palavras
                        * levenshtein, ngrams
                    * dependente do léxico/dicionário/corpura usado
                        * maior parte do trabalho realizado é sobre a criação de léxicos abrangentes o suficiente, ou adaptados ao documento
                * modelos de erro
                    * foco na probabilidade de erro entre caracteres, inves de foco nas palavras inteiras
                    * começou por permitir edições de 1 caractere, tendo propostas recentes permitido multiplos
                    * uso de um lexico para o suporte em algumas das hipoteses
                * maquinas de estado finitas com pesos
                    * usado muitas vezes juntamente com os modelos de erro
                    * pesos podem ser uma combinação de varios metodos, como hipotese do modelo de erro, distantica de similaridade, probabilidade de ser uma variação de uma palavra ,etc.
                * modelos de linguagem baseados em tópicos
                    * balancear os pesos tendo em conta o topico do documento
                    * primeiramente é preciso criar uma lista de topicos conhecidos
                    * criar algoritmo para decisao do topico de um documento
                    * adaptar lexico para atribuir topicos às palavras
                * outros modelos
                    * SVM, word2vec, etc.
        * dependente de contexto
            * pode tratar de problemas de palavras não reais, ou de palavras erradas
            * modelos de linguagem
                * estatisticos
                    * evolução de modelos de erro para consideram contexto
                    * contexto pode utilizado conseguido através dos vizinhos diretos, ou de combinações de palavras dentro do documento ou num léxico (n grama), ou para probabilidade de n-grama aparecer num dado contexto
                * Neural Network
                    * word embedding
                    * criaçao de classificadores probabilisticos
                    * calculam probabilidade de uma palavra ser escolhida numa dada sequencia
            * ML baseado em caracteristicas
                * escolha de um numero limitado de features
                    * distancia de edição ou similaridade
                    * frequencia de unigrama
                    * frequencia de n-grama
                    * confusion weight
                    * confiança do OCR
                * classificaçao utilizando um modelo estatistico
            * sequence-to-sequence (Seq2Seq)
                * transformação do texto como um todo
                * machine translation
                * tradicional
                    * transformação de palavras
                * Neural Network
                    * transformação da frase
                * casos de mistura em que utilizam transformação de caracter
* apresentadas varias metricas de avaliação
    * Precisão
    * recall (acertos relevantes)
    * F-Score
    * BLEU (para Machine translation)
    * ER
    * Acerto (accuracy)
* conjunto de toolkits para pos processamento
* conjunto de testes em diferetens datasets


# Segmentação de documentos

## Document image segmentation using discriminative learning over connected components : https://dl.acm.org/doi/abs/10.1145/1815330.1815354 - 2010
* resumo de segmentação de páginas
    * baseado em blocos
        * dividir pagina em blocos e atribuir a cada bloco uma classe
        * metodo por Wang et al.
            * divisao de pagina em blocos
            * criação de vetores representantes dos blocos
            * decisor para atribuir classe aos blocos
        * muito dependente da daivisao inicial em blocos
    * baseado em pixeis individuais
        * classificação de pixeis
        * não limitado a regiões quadradas
        * lento
* método proposto
    * ML
    * categorização de componentes ligados
    * diferente dos ultimos dois métodos e independete de segmentação inicial
    * conjunto limitado de classes, mais poderiam ser adicionadas no set de treino
    * vetor de caracteristicas robusto
        * objeto reescalado
        * metadados da forma do objeto
            * comprimento e largura normalizados
            * aspect ratio
            * numero de pixeis na area reescalada em relação ao numero total da area reescalada
        * informacao de contexto
            * uma certa quantidade da vizinhança do componente é juntada
    * classificador MLP (multi-layer perceptron) auto tuned
    * resultados
        * segmentação de imagens mais flexivel do que o estado da arte comparado

## A comprehensive survey of mostly textual document segmentation algorithms since 2008 : https://www.sciencedirect.com/science/article/pii/S0031320316303399 - 2017
* divisão entre diferentes tipos de algoritmos 
    * grupos tipicos
        * top-down : segmentar a partir da pagina
        * bottom-up : a partir de escalas mais pequenas, tenta aglomerar elementos em conjuntos maiores ate passar o documento inteiro
            * pixeis
            * componentes conectadas
            * alternativo
        * hibrido
    * grupos da survey
        * algoritmos especificos para um tipo de layout
            * tipo que assumem as caracteristicas do layout
            * tipo que utilizam filtros para realçarem as regioes de um documento
            * tipo que procura as delimitações das regioes do layout no docmento
        * algoritmos versateis mas que necessitam de parametros extra para se adaptarem ao layout
            * clustering
            * análise de funções
            * classificação
        * algoritmos totalmente flexiveis
            * hibridos : complexos e normalmente sem grandes melhorias
            * redes neuronais
    * grupo 1 - layout especifico
        * algoritmos especificos para um tipo de layout que assumem layout
            * mais rapidos
            * muito restritivos
            * nas condições certas apresentam melhores resultados do que os mais flexiveis
            * tipos
                * gramáticas
                    * layout é descrito segundo um conjunto de regras
                * projeção de perfis
                    * criação de um perfil usando quadrados que depois é projetado sobre o documento e sujeito a heuristicas e analises probabilistacas para deteção de erros
        * algoritmos baseados em filtros
            * assumem que as linhas sao retas e bem orientadas
            * tipos
                * morfologias
                    * erosao e dilatação para identificação de imagens
                    * RLSA (Run-Length Smoothing Algorithm)
                        * conversao de pixeis de 0 para 1 quando o numero de 0 adjacentes é menor que um dado limite
        * baseado na identificação de linhas retas
            * calculo das linhas de texto para segmentação
            * alguns algoritmos para reconhecimento de linhas
                * Hough transformation
    * grupo 2 - layout restringido por parametros
        * mais flexiveis do que o anterior
        * baseado em clustering
            * mais popular
            * geométrico
                * elementos base os componentes conectados 
                * features principais geometricas
                    * distancia
                    * area
                    * densidade
                * outras
                    * distribuicao geometrica
                    * cor
            * textura
                * baseado nas caracteristicas ao nivel dos pixeis
            * caracteristicas genericas
                * junção entre segmentação de blocos e clustering de features
        * baseado em análise de funções
            * otmização de função de custo
        * baseado em classificação
            * segundo mais popular
            * uso de MLP, SVM
            * baseado em textura
            * baseado em caracteristicas
                * mais comum
                * uma das caracteristicas tende a ser a cor
                * features podem ser predefinidas ou usados modelos para automaticamente calcular e depois escolher as melhores features
    * grupo 3 - layout (potencialmente) não restrito
        * hibridos
        * combinados
        * redes neuronais
    * discussao, metricas de avaliação, estatisticas e resultados

## Multi-Scale Multi-Task FCN for Semantic Page Segmentation and Table Detection : https://ieeexplore.ieee.org/abstract/document/8269981 - 2017
* metodo utilizando multiplas CNN para segmentação de documentos em classes de texto e nao texto
* foco tambem na indentificacao de tabelas

    


# OCR validação
On OCR ground truths and OCR post-correction gold standards, tools and formats : https://dl.acm.org/doi/10.1145/2595188.2595216

An open-source OCR evaluation tool : https://dl.acm.org/doi/10.1145/2595188.2595221

OCR performance prediction using cross-OCR alignment - https://ieeexplore.ieee.org/document/7333823

Performance Evaluation and Benchmarking of Six-Page Segmentation Algorithms - https://ieeexplore.ieee.org/document/4407728


# OCR trabalhos relacionados

Digitization of Data from Invoice using OCR - https://ieeexplore.ieee.org/document/9754117





# Algoritmos


# Estrutracao de jornais:

## Old Sinhala Newspaper Article Segmentation for Content Recognition Using Image Processing : https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9833047 - 2021 + Procedural approach for content segmentation of old newspaper pages : https://ieeexplore.ieee.org/abstract/document/8300390 - 2017
* processo de remoção de imagens do jornal, seguido da remoção de delimitadores; permite a identificação das linhas brancas de separação entre artigos
* uso de ML apenas para tratamento de imagem
* resultados muito bons para jornais bastante complexos, embora quantidade de casos de teste muito reduzido (~250)
    * algoritmos a estudar:
        * Douglas-Peucker algorithm
        * Otsu binarization
        * Hough line
        * RLSA 
        * Sobel X
    * referencias a varios artigos sobre limpeza e melhoria de imagens com danos causados por idade e má digitalização

## Newspaper Article Extraction Using Hierarchical Fixed Point Model : https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6831009 - 2014
* forte uso de ML para a indetificação segmentação de artigos num jornal
* imagens utilizadas nao tem em conta danos de idade
* utilizacao de processamento de imagem para remocao de delimitadores numa fase inicial e criacao dos diferentes blocos de texto e imagem
* utilizacao de numero compacto mas logico de parametros na funcao de labeling dos blocos, incluindo imagens
* potencial de adaptabilidade para diferentes layouts, visto nao seguir heuristicas especificas
* resultados bons, mas sob um datasete muito reduzido (~45)
* bastantes referencias a artigos sobre estado da arte, assim como uso de tecnologias ja criadas no projeto

* pre processamento
    * binarização
    * remoção de linhas (delimitadores) tendo em conta o aspect ratio dos componentes ligados
    * uso do projeto leptonica para segmentação entre texto e graficos
    * resultado : blocos retangulares categorizados como texto ou imagem
* 2º fase - calculo de vizinhos
    * uso de limiar q define numero maximo de vizinhos em cada direção
    * diferentes limares para categorização de bloco e extração de artigo
        * para extracao de artigo maior
* 3º fase - classificação de bloco
    * uso de caracteristicas de aparacencia
        * altura, comprimento
        * altura do componente ligado mais alto
        * aspect ratio
        * ratio de pixeis preto e branco
    * vizinhança como resto das caracteristicas
    * Kernel logistic regression para classificação
* 4º fase - extração de artigos
    * para cada bloco de tipo heading, assume-se um artigo e itera-se o processo
    * blocos são classificados entre artigo e não artigo usando como base o heading


## Google Newspaper Search – Image Processing and Analysis Pipeline : https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=5277572 - 2009
* da google
* relativamente desatualizado, utiliza heuristicas e tecnicas sem uso de ML
* supostamente utilizado num grande numero de jornais mas sem grande detalhe sobre os resultados sem ser 90% de eficacia na segmentacao e 80% no OCR (se apenas nos exemplos do artigo ou no total nao é explicito)
* algoritmos a estudar:
    * image binarization
    * morphological grayscale reconstruction


## Instance Segmentation of Newspaper Elements Using Mask R-CNN : https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8999273 - 2019
* completamente focado em ML
* uso de CNN com mascara
* resultados que ajudariam na segementação do jornal, mas seriam necessitariam ainda de serem processados localmente
* modulo generalista, agnostico de linguagens
* dataset nao muito grande (~840)
* Modelo não usa resultados de OCR, fazendo ele proprio uma primeira fase de identificação de zonas candidatas de ter conteudo, e so depois sao essas regioes classificadas, e aplicadas mascaras ao nivel dos pixeis (nao limitadas a regioes quadrangulares)

    
## Europeana Newspapers OCR Workflow Evaluation : https://dl.acm.org/doi/10.1145/2809544.2809554 - 2015
* projeto europeu para popularizar praticas para digitalização de jornais usando OCR

## Fully Convolutional Neural Networks for Newspaper Article Segmentation : https://ieeexplore.ieee.org/abstract/document/8270006 - 2017
* redes convolucionais para segmentação de artigos
* 3 fases
    * extraçao de features
    * upscale e segmentação
    * separação entre pixeis background e artigo


## Combining Visual and Textual Features for Semantic Segmentation of Historical Newspapers : https://arxiv.org/abs/2002.06144v4 - 2020
* modificacao de uma CNN para em conjunto com imagem, receber text embeddings
* uniao de caracteristicas visuais com caracteristicas textuais do documento e dos blocos

## Article Segmentation in Digitised Newspapers with a 2D Markov Model : https://ieeexplore.ieee.org/document/8978066 - 2019
* focado em heuristicas
* modelo de markvo 2d
* permite segmentação em artigos tendo em conta a ordem de leitura


## ordenaçao de caixas
https://www.researchgate.net/publication/2564797_High_Performance_Document_Layout_Analysis - Naive
https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9413256 - ML
https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7351614 - Grafo


# Alinhamento de texto

Creating an Improved Version Using Noisy OCR from Multiple Editions : https://ieeexplore.ieee.org/document/6628604 - 2013