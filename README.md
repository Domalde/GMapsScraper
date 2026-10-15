# GMapsScraper

Coleta dados de estabelecimentos do Google Maps a partir de um termo de busca
(ex.: `restaurante maceió`) e salva em CSV: nome, categoria, endereço, telefone,
site, nota, nº de avaliações, latitude, longitude e link.

## Instalação

Requer Python 3.8+ e o Google Chrome instalado.

```bash
pip install -r requirements.txt
```

O Selenium 4 baixa automaticamente o `chromedriver` compatível com o seu Chrome,
não é preciso instalar à parte.

## Uso

```bash
python GMapsData.py "restaurante maceió"
python GMapsData.py "padaria recife" --max 50 --saida padarias.csv --headless
```

| Opção        | Descrição                                   |
|--------------|---------------------------------------------|
| `--max N`    | limita a N resultados (padrão: todos)       |
| `--saida`    | arquivo CSV de saída (padrão: `resultados.csv`) |
| `--headless` | roda sem abrir a janela do Chrome           |

O CSV usa `;` como separador e UTF-8 com BOM, para abrir direto no Excel.

## Como funciona

1. Abre a busca no Google Maps e rola a lista de resultados (`div[role="feed"]`)
   até aparecer "Você chegou ao final da lista." ou atingir `--max`.
2. Guarda o link de cada resultado e abre um por um.
3. Lê os dados pelos atributos estáveis da página (`data-item-id="address"`,
   `data-item-id="phone:tel:…"`, `data-item-id="authority"`), em vez de XPaths
   absolutos, que quebravam a cada mudança no layout do Maps.

O Google altera o HTML do Maps de tempos em tempos. Se algum campo vier vazio,
ajuste o seletor correspondente nos métodos `get_*` de `GMapsData.py`.
