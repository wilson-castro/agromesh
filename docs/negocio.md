# O negócio

Este documento explica que problema o AgroMesh resolve e como ele é usado, sem entrar em detalhes técnicos. A parte técnica está em [arquitetura.md](arquitetura.md) e [servicos.md](servicos.md).

## O problema

Uma fazenda que irriga as plantações precisa decidir quando e quanto regar. Regar de menos deixa a planta sem água. Regar demais desperdiça água e energia. Para decidir bem, quem cuida da fazenda precisa saber, a cada momento, como está a terra em cada área e quanta água já foi usada.

O AgroMesh junta essas informações num painel só. Ele recebe as medições dos equipamentos espalhados pela fazenda, guarda o histórico e permite abrir ou fechar a irrigação de longe.

## A fazenda simulada

A fazenda do projeto tem duas áreas de plantio, chamadas de talhões (`talhao-a` e `talhao-b`), e uma sede. Os equipamentos ficam assim.

| Onde | Equipamento | O que faz |
|---|---|---|
| Sede | Estação meteorológica (`estacao-01`) | Mede temperatura e umidade do ar, vento e chuva. |
| Cada talhão | Sensor de solo (`solo-a`, `solo-b`) | Mede a umidade e a temperatura da terra. Avisa na hora quando a terra fica seca. |
| Cada talhão | Válvula de irrigação (`valvula-a`, `valvula-b`) | Libera ou corta a água do talhão. Informa a vazão e o total de litros já usados. |

Os equipamentos não são reais. Cada um é um programa que inventa medições parecidas com as de verdade. A umidade do solo, por exemplo, sobe e desce num ciclo de 4 minutos. Por isso o alerta de solo seco aparece várias vezes durante uma demonstração.

## O que a pessoa faz no painel

- Acompanha ao vivo a umidade de cada talhão, a vazão das válvulas e a temperatura do ar.
- Recebe um alerta quando a umidade de um talhão cai abaixo de 25%.
- Abre ou fecha uma válvula e escolhe a vazão, em litros por minuto.
- Desliga uma válvula para simular um defeito. O painel passa a mostrar esse equipamento como fora do ar.
- Consulta o histórico para responder a quatro perguntas.

| Pergunta | Para que serve |
|---|---|
| Qual talhão está mais seco? | Escolher onde irrigar primeiro. |
| Quanta água cada talhão usou? | Controlar o consumo e o custo. |
| Como variou a temperatura do ar? | Entender se o dia está quente e a terra vai secar mais rápido. |
| Quantos alertas de seca cada talhão teve? | Descobrir qual área precisa de mais atenção. |

As perguntas podem olhar os últimos 5 minutos, 15 minutos, a última hora ou as últimas 24 horas.

## O que o sistema não faz

- Ele não irriga sozinho. A decisão de abrir a válvula é sempre de quem opera o painel.
- Na simulação, abrir uma válvula não muda a umidade medida no solo. Cada equipamento simulado funciona por conta própria.
- O contador de litros fica guardado na própria válvula. Se ela reiniciar, a conta de consumo daquele período sai errada.
