# Nova proposta de arquitetura para prompts

Vamos propor uma arquitetura de prompts baseada em foco, de forma a diminuir o tamanho do contexto, auxiliar o SLM e com sorte optimizar a eficiência do agente.

## Embasamento biológico:
Os seres humanos conseguem armazenar em média 5 informações ao mesmo tempo, sendo 1 em foco, e 4 como pequenos ruidos. Vamos tentar trazer essa visão para o agente de código.

## Diferênça de pensamento:
Atualmente, todas as pesquisas tentam aglutinar o conhecimento em um prompt cheio de regras e etapas. Modelos gigantescos podem lidar com isso, mas estamos tentando fazer isso com SLMs.
A forma de fazer isso é seguir o embasamento biológico: precisamos fazer o modelo se concentrar obrigatóriamente em uma tarefa simples por vêz.

# Ideia principal:
Podemos retratar essa ideia revisando como um ser humano programa:
1º vamos ler qual é nossa tarefa. e.g: corrija o erro X
2º vamos compreender o que é o erro X (repare que agora não importa mais a tarefa, importa apenas o erro X).
3º vamos lembrar vagamente o que estamos fazendo: a sim, queremos resolver/corrigir esse erro. Precisamos então não apenas entender o erro, mas saber o que está relacionado com ele. Então vamos procurar arquivos relacionados com ele (esse é um passo complexo, pois envolve uma pequena volta ao estado anterior, como se o foco saísse de 100% na tarefa e ficasse 80% nela. Isso pode exigir um prompt maior).
4º Temos todos esses arquivos, precisamos saber o que eles fazem. (não sabemos mais o motivo que estamos fazendo isso, apenas queremos entender profundamente cada linha de cada arquivo, e suas relações, se encontrarmos um eventual erro vamos sinalizar, mas não é nosso foco. Precisa ser uma instrução simples em chunks do arquivo, pois esses arquivos podem ser muito grandes.)
5º agora que temos documentado "linha a linha" do arquivo, vamos ver qual era a tarefa principal: a sim, corrigir o erro X, e sabemos por causa de 2 que esse erro ocorre principalmente por W/Y/Z.
6º vamos procurar nas documentações do arquivo se eu vejo algo sobre W/Y/Z. (não sabemos mais nada, apenas procuramos W/Y/Z)
7º não achei nada sobre W/Y/Z. Qual era a tarefa primária? a sim, corrigir o erro X
8º tem algum erro documentado? vamos ver.
9º procurando por erros na documentação (não sabemos mais nada, apenas queremos procurar erros)
10º encontramos um erro! Vamos sinalizar isso.
11º Qual era a tarefa principal? a sim, corrigir o erro X. Temos um erro que encontramos em 10.
12º o erro encontrado é o erro X? Sim! E agora? a sim, corrigir o erro X.
13º segundo a tarefa eu devo corrigir o erro X, eu tenho a seguinte documentação sobre o erro X: ... Acredito então que eu posso fazer um plano para corrigir o erro X.
14º temos que separar essa documentação de código em módulos, com um pequeno resumo sobre o que cada módulo faz, e quando eu quiser mais detalhes sobre um módulo ai sim eu vejo a documentação daquele módulo. (assim não temos que ficar com toda a documentação, apenas trabalhamos com resumos delas, e abstrações. e.g: eu tenho uma função F que me devolve o token de acesso. Se em algum momento eu precisar de algo específico, ai sim eu vou ver mais informações sobre isso, mas no geral eu preciso apenas saber que aquele bloco significa: obter o token de acesso).
15º (após várias e várias chamadas) documentação modularizada, consigo ter uma visão completa do sistema em poucas frases. Qual era a tarefa principal mesmo? a sim, corrigir o erro X
16º O erro X está no bloco B, deixa eu ver mais informações sobre ele.
17º O bloco B apresenta um loop, um if, uma atribuição. O erro X eu tenho documentado que ele geralmente ocorre por conta de atribuições erradas.
18º respondendo a pergunta: a atribuição do bloco B pode gerar um erro? Pode se a variável V que é atribuída a B não for um vetor. {consultar o que eu sei sobre V}.
19º V não é um vetor.
20º Qual era a tarefa principal? a sim, corrigir o erro X. Eu sei que X acontece por causa de atribuições erradas. B pode ter um erro se V não for um vetor e V não é um vetor. V é a causa do erro? Possívelmente sim.
21º preciso tentar entender o porque V não é um vetor, quando ele deveria ser. {consultar o que eu sei sobre B para entender o que está acontecendo aqui}
22º B tenta fazer uma múltiplicação de matrizes. V deveria ser uma matriz, mas aparentemente é um float.
23º Qual é a tarefa principal? a sim, corrigir o erro X. Eu sei que X é causado geralmente por atribuições erradas. B tenta fazer uma multiplicação de matrizes, e V deveria ser uma matriz. V não é um vetor.
24º Causa do erro encontrada. Precisamos agora propor uma solução. Eu não sei o que o usuário desejaria fazer nesse caso.
25º informa o resultado até aqui para o usuário.
26º usuário informa que deseja então fazer uma alteração: deve ser uma função de múltiplicação de matriz por escalar.
27º Tarefa primária alterada. Nova tarefa: Fazer alteração de múltiplicação de matriz no bloco B para multiplicar matriz por escalar.
... (a análise segue como te demonstrei, até chegar na tarefa final)
Nº Agora preciso formular o código final:
```language...```
FIM.

# Detalhamento da implementação:
sempre precisamos segurar múltiplos estados, e coordena-los. Isso geralmente envolve um grafo, e uma máquina que caminha entre estados, cria novos estados, e direciona a conversa.
O motor dessa máquina é uma abstração de outro agente llm, que observa o mundo de uma forma diferênte, como um guia.

a ideia do agente do grafo é que ele construa os prompts para o sub-agente. Não construir prompts inteiros, mas organizar templates de prompts.
O sub-agente pede as informações, e o agente do grafo de estados vai direcionando.
Ex:
Inicio -> agente de estados conhece um estado: o da tarefa atual -> passa um prompt para o modelo base instruíndo ele sobre a tarefa.

O modelo vai responder com pedidos sobre a tarefa segundo uma lista de pedidos que ele pode fazer (como ferramentas)
Cada pedido cria um novo estado. Por exemplo:
Estado tarefaPrincipal -> estadoExplorar erro.

Vamos manter as conexões entre estados seguindo um algorítimo de starvation: conxões pouco utilizadas vão sumindo. Um nó ilha é deletado, e sua informação é resumida em um banco de informações (Log)

O modelo do grafo ele tem que ser crítico, as vezes o modelo vai pedir algo que não é exatamente o nome do nó que já existe, mas é para a mesma tarefa.

O modelo do grafo sabe que o objetivo dele é conduzir o subagente, mas o subagente é quem vai andando livremente. A única coisa é que o modelo do grafo sabe quando o modelo agente finalizou uma tarefa, e ele faz o "restart", reconduzindo ele para a tarefa original, coletando todas as informações que ele produziu, e "resumindo-as" utilizando outro agente, um resumer, para conseguir construir essa ideia de "caixas de conhecimento abstraído".
Vê como que a tarefa do agente é mais simples e direta, mas com ações simples e diretas acabamos conseguindo resultados emergente.

## Comentários:
Essa abordagem é totalmente diferênte da atual forma como o opencode é pensado e funciona, mas acredito que seria uma forma de conseguir além de melhores resultados, conseguir uma ferramenta que consiga reduzir drasticamente custos ao utilizar slms ao invés de llms.