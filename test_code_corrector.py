a = """Eu como usuário da minha unidade com acesso à função preciso cadastrar formulários para serem utilizados no cadastro de editais (fica evidente que a rota que exibe esse formulário deve ser protegida).
**Critérios de aceite:**
Ter um formulário padrão com os seguintes campos pré-selecionados:
Título do Edital; Descrição; Valor total; Valor máximo por proposta; Quantidade de dias para prestação de contas; Quantidade de assessores; Data inicial de recebimento; Data final de recebimento; Exibir valor; Linha; Disponibilizar botões para cancelar, salvar como rascunho e salvar formulário; 
Ao salvar, exigir um nome para o formulário para ser utilizado ao criar os editais;
É interessante observar que: nosso projeto não tem um formulário fixo para criarmos editais. É passado um json, e com ele nós vamos gerar o formulário de forma dinâmica. Portanto, o que estamos fazendo é criar o formulário que servira para criar editais. Com essa informação vamos falar: "para você criar um edital, você deverá informar o nome dele, a data, etc...". Estamos fazendo o formulário para criar editais.
Mantenha a coesão visual com o restante do sistema, utilizando os mesmos estilos e componentes já existentes quando possivel, ou estilizando os componentes novos para serem visualmente coerentes com o restante do sistema."""

print(a.replace('\n', '\\n'))