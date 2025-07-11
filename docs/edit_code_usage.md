# Funcionalidade edit_code

A funcionalidade `edit_code` permite que o LLM modifique código existente de forma precisa e segura.

## Como usar

### Formato do comando

```json
{
    "command": "edit_code",
    "args": ["caminho/arquivo.py", "codigo_antigo", "codigo_novo"]
}
```

### Parâmetros

1. **file_path**: Caminho para o arquivo a ser editado
2. **old_code**: Trecho exato do código que deve ser substituído
3. **new_code**: Novo código que substituirá o trecho antigo

### Exemplos práticos

#### Exemplo 1: Corrigir valor de variável
```json
{
    "command": "edit_code",
    "args": [
        "src/config.py",
        "DEBUG = True",
        "DEBUG = False"
    ]
}
```

#### Exemplo 2: Adicionar validação a um método
```json
{
    "command": "edit_code",
    "args": [
        "src/user.py",
        "def set_email(self, email):\n    self.email = email",
        "def set_email(self, email):\n    if '@' not in email:\n        raise ValueError('Email inválido')\n    self.email = email"
    ]
}
```

#### Exemplo 3: Refatorar método Java
```json
{
    "command": "edit_code",
    "args": [
        "src/main/java/User.java",
        "public String getName() {\n    return null;\n}",
        "public String getName() {\n    return this.name != null ? this.name : \"Unknown\";\n}"
    ]
}
```

## Vantagens sobre outras abordagens

### Vs. edição por linha
- ✅ Não precisa especificar números de linha
- ✅ Mais robusto contra mudanças no arquivo
- ✅ Trabalha com o conteúdo real do código

### Vs. recriar arquivo completo
- ✅ Mais eficiente para pequenas mudanças
- ✅ Preserva formatação do resto do arquivo
- ✅ Menor chance de introduzir erros

## Recursos de segurança

### Validação de ambiguidade
O sistema verifica se o `old_code` aparece apenas uma vez no arquivo:
- Se não encontrar: retorna erro
- Se encontrar múltiplas vezes: retorna erro pedindo trecho mais específico
- Se encontrar exatamente uma vez: aplica a substituição

### Correção automática
Após a edição, o sistema:
1. Detecta a linguagem do arquivo
2. Aplica correções automáticas se disponível
3. Relata as correções aplicadas

### Atualização de contexto
Após editar um arquivo, o sistema:
1. Atualiza a symbol table se possível
2. Mantém consistência com outras análises

## Tratamento de aspas e caracteres especiais

### Problema comum: Aspas conflitantes
❌ **Problemático:**
```json
{
    "command": "edit_code",
    "args": ["src/main.py", "print("hello")", "print("Hello, World!")"]
}
```

### Soluções:

#### 1. Escape de aspas internas
✅ **Correto:**
```json
{
    "command": "edit_code",
    "args": ["src/main.py", "print(\"hello\")", "print(\"Hello, World!\")"]
}
```

#### 2. Uso de aspas simples
✅ **Correto:**
```json
{
    "command": "edit_code",
    "args": ["src/main.py", "print('hello')", "print('Hello, World!')"]
}
```

#### 3. Mistura estratégica de aspas
✅ **Correto:**
```json
{
    "command": "edit_code",
    "args": ["src/main.py", 'print("hello")', 'print("Hello, World!")']
}
```

### Caracteres especiais que precisam de escape

| Caractere | Escape necessário | Exemplo |
|-----------|-------------------|---------|
| `"` | `\"` | `"Hello \"World\""` |
| `\` | `\\` | `"C:\\\\Users\\\\file"` |
| `\n` | `\\n` | `"Line 1\\nLine 2"` |
| `\t` | `\\t` | `"Tab\\there"` |

### Exemplo completo com escapes
```json
{
    "command": "edit_code",
    "args": [
        "src/utils.py",
        "def format_path(path):\n    return path",
        "def format_path(path):\n    return path.replace('\\\\', '/')"
    ]
}
```

### 1. Use trechos específicos
❌ Ruim:
```json
{"command": "edit_code", "args": ["file.py", "return x", "return x + 1"]}
```

✅ Bom:
```json
{"command": "edit_code", "args": ["file.py", "def calculate():\n    return x", "def calculate():\n    return x + 1"]}
```

### 2. Inclua contexto suficiente
❌ Ruim (pode ser ambíguo):
```json
{"command": "edit_code", "args": ["file.py", "self.value = 0", "self.value = 42"]}
```

✅ Bom:
```json
{"command": "edit_code", "args": ["file.py", "def __init__(self):\n    self.value = 0", "def __init__(self):\n    self.value = 42"]}
```

### 3. Use `open_file` antes de editar
Sempre leia o arquivo primeiro para garantir que você está usando o trecho correto:

```json
{"command": "open_file", "args": ["src/user.py"]}
```

Depois:
```json
{"command": "edit_code", "args": ["src/user.py", "...", "..."]}
```

## Tratamento de erros

### Arquivo não encontrado
```
❌ Erro: Arquivo 'inexistente.py' não encontrado
```

### Trecho não encontrado
```
❌ Erro: Trecho de código não encontrado no arquivo 'file.py'
```

### Trecho ambíguo
```
❌ Erro: Trecho ambíguo encontrado 3 vezes no arquivo 'file.py'. Use um trecho mais específico.
```

## Integração com outras ferramentas

O comando `edit_code` se integra bem com:
- `open_file`: Para ler antes de editar
- `search_dir`: Para encontrar onde fazer mudanças
- `run_test`: Para verificar se as mudanças funcionam
- `list_files`: Para navegar pela estrutura

## Exemplo de fluxo completo

```json
// 1. Buscar arquivo relevante
{"command": "search_dir", "args": ["UserService", "src"]}

// 2. Ler o arquivo encontrado
{"command": "open_file", "args": ["src/service/UserService.java"]}

// 3. Editar método específico
{"command": "edit_code", "args": [
    "src/service/UserService.java",
    "public User findById(Long id) {\n    return null;\n}",
    "public User findById(Long id) {\n    return userRepository.findById(id).orElse(null);\n}"
]}

// 4. Verificar se funciona
{"command": "run_test", "args": ["mvn test -Dtest=UserServiceTest"]}
```
