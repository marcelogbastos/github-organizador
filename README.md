# GitHub Dashboard

Dashboard único com **todos os seus repositórios** e **seus favoritos (stars)**. Python 3.10+, sem pip, sem dependências.

## Estrutura

```
src/github-dashboard.py     coleta pela API do GitHub e gera o HTML
templates/dashboard.html    template do dashboard (HTML + CSS + JS, sem bibliotecas externas)
saida/dashboard.html        resultado: abra no navegador (gerado)
saida/dados/dados.json      dados coletados (gerado)
```

`saida/` é ignorada pelo git: pode conter repositórios privados.

## Executar

```powershell
python src/github-dashboard.py      # usa GITHUB_TOKEN ou o token do GitHub CLI (inclui privados)
Start-Process .\saida\dashboard.html
```

Opções:

| Opção | O que faz |
|---|---|
| `--user NOME` | Outro usuário (padrão: marcelogbastos) |
| `--public-only` | Ignora tokens e coleta só repositórios públicos |
| `--no-languages` | Pula o detalhamento de linguagens por repositório (menos chamadas à API) |
| `--from-json saida/dados/dados.json` | Regenera o HTML sem acessar a API (útil ao editar o template) |
| `--output PASTA` | Pasta de saída |

O token vem de `GITHUB_TOKEN` ou, se ausente, do GitHub CLI (`gh auth login`); sem nenhum dos dois, só repositórios públicos são coletados e o script avisa. O token é lido apenas pelo Python e nunca é gravado no HTML ou no JSON. Os dados só são gravados depois de a coleta terminar.

## O que o dashboard oferece

- **Visão geral**: indicadores (repositórios, ativos, stars, issues, privados), linguagens por repositório ou por bytes de código, linguagens dos favoritos, atividade e favoritos por mês, projetos por ano, recência, itens que precisam de atenção (sem descrição, licença, tópicos, parados), mais estrelados, atividade recente, licenças e tópicos. Gráficos e indicadores são clicáveis e levam à lista filtrada.
- **Meus projetos**: tabela ou cards, filtros (linguagem, tópico, situação, status), ordenação por coluna, nota de saúde (descrição, licença, tópicos, push recente), exportação CSV.
- **Favoritos**: filtros por linguagem, tópico, licença, categoria, status de estudo, arquivamento, stars mínimas e último push; ordenação e paginação.
- **Detalhes** (clique em qualquer repositório): métricas, linguagens, saúde, links, copiar `git clone`, e sua organização pessoal (categoria, status, notas, destaque).
- **Busca global**: `Ctrl K` ou `/`.
- Tema claro/escuro (segue o sistema), paleta validada para daltonismo, tabelas alternativas aos gráficos, layout responsivo.

## Organização pessoal

Categorias, status, notas e destaques ficam no armazenamento do navegador (não alteram o GitHub nem sincronizam entre dispositivos). Use **Dados → Backup** antes de trocar de navegador ou de pasta e **Importar backup** para restaurar. Notas salvas pela versão antiga (só favoritos) são aproveitadas automaticamente. Para um endereço local estável:
`python -m http.server 8000 --bind 127.0.0.1 --directory saida` e abra http://127.0.0.1:8000/dashboard.html .

Fontes: https://docs.github.com/en/rest/repos/repos#list-repositories-for-the-authenticated-user · https://docs.github.com/en/rest/activity/starring
