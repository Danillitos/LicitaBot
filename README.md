# Automação de Inclusão de Planilhas Orçamentárias no TransfereGov

Este repositório contém uma automação desenvolvida em Python para auxiliar consultorias técnicas, engenheiros e municípios na inclusão de planilhas orçamentárias no sistema governamental TransfereGov.  
O objetivo é reduzir o tempo gasto no processo manual, que costuma ser lento, repetitivo e sujeito a erros.

## Objetivo

A aplicação lê planilhas orçamentárias, interpreta seus dados e automatiza a inserção das informações no TransfereGov.  
Como a plataforma utiliza uma arquitetura SPA, a automação foi estruturada para lidar com mudanças dinâmicas na interface e possíveis alterações de elementos ao longo do uso.

## Tecnologias Utilizadas

- Python  
- Pandas  
- PyAutoGUI  
- Selenium WebDriver  

## Características do Projeto

- Tratamento de atualizações dinâmicas da interface devido ao comportamento SPA.  
- Automação de etapas repetitivas do preenchimento manual.  
- Manipulação e limpeza de dados utilizando Pandas.  
- Interação com navegador via Selenium e controles secundários via PyAutoGUI.  

## Estrutura Geral da Automação

- Leitura e preparação dos dados das planilhas.  
- Mapeamento e identificação dos campos necessários no sistema.  
- Execução da automação de navegação e preenchimento.  
- Logs e verificações para garantir que a operação foi concluída corretamente.

## Requisitos

- Python 3.10 ou superior  
- Driver compatível com o navegador utilizado  
- Dependências listadas em `requirements.txt`  

## Execução

1. Instale as dependências:  
   ```bash
   pip install -r requirements.txt

2. Execute o script principal

## Aviso

A automação depende diretamente da interface atual do TransfereGov. Alterações futuras na plataforma podem exigir ajustes nos seletores, fluxos ou validações.


