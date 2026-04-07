# ASCM - Sistema Automatizado de Limpeza e Arrefecimento de Painéis Fotovoltaicos

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Engineering](https://img.shields.io/badge/Engineering-Control%20%26%20Automation-blue)](https://github.com/lucasekroth/auto-cleaning-solar-panel)

O **ASCM** (Automated Self-Cleaning and Cooling Mechanism) é um projeto de Engenharia de Controle e Automação focado em maximizar a eficiência de sistemas de energia solar fotovoltaica. O sistema combate os dois principais vilões da geração solar: o **soiling** (acúmulo de sujeira) e o **superaquecimento** das células.

## 🚀 Funcionalidades

- **Limpeza Automatizada:** Sistema de aspersão combinado com rodo motorizado (wiper) para remoção de poeira e crostas de sujeira (*hard scale*).
- **Arrefecimento Inteligente:** Monitoramento térmico em tempo real para acionar o resfriamento quando a temperatura ultrapassa os níveis ideais.
- **Sensoriamento em Tempo Real:** 
  - Comparação diferencial de potência entre o painel principal e um de referência.
  - Monitoramento de temperatura e condições ambientais.
- **Gestão Hídrica:** Projetado para uso otimizado de água, com foco em baixo custo e alta eficácia.

## 📊 Motivação Técnica

A eficiência de um painel solar é severamente afetada por fatores externos:
*   **Soiling:** O acúmulo de poeira pode reduzir a eficiência em até **7,84% por semana**. Em períodos de seca, as perdas podem ultrapassar **50%**.
*   **Temperatura:** Para cada grau Celsius acima de 25°C, a eficiência do módulo decresce entre **0,5% e 0,6%**.
*   **Aumento de Eficiência:** Estudos (Geetha et al., 2024) demonstram que o uso de ASCM pode elevar a eficiência de saída em até **14,81%**.

## 🛠️ Tecnologias e Componentes

Com base na arquitetura definida para o protótipo:

### Eletrônica e Controle
- **Microcontrolador:** Arduino Uno.
- **Sensores:**
    - Corrente/Tensão: INA219.
    - Temperatura: Termopar Impermeável (feedback em malha fechada).
- **Atuadores:**
    - Motores: DC com Caixa de Redução.
    - Driver: Ponte H L298N.
    - Hidráulica: Mini-bomba 12V e bicos aspersores.

### Design e Software
- **Modelagem 3D:** Autodesk Inventor (design mecânico e simulação).
- **Firmware:** C++/Arduino (lógica de controle e sensoriamento).
- **Interface/Monitoramento:** Python (Dashboard para visualização de parâmetros).
- **Fabricação:** Impressão 3D (FDM) para peças estruturais e personalizadas.

## 📂 Estrutura do Repositório

```text
├── docs/            # Documentação, apresentações e artigo (LaTeX)
├── firmware/        # Código fonte do microcontrolador (C++/Arduino)
└── hardware/        # Design 3D (Inventor) e esquemas elétricos
```

## 👥 Autores

*   **César Kerber**
*   **Lucas Ekroth**
*   **Paulo Rangel**

---
*Projeto desenvolvido como parte do Projeto Integrador do curso de Engenharia de Controle e Automação.*
