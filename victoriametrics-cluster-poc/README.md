# VictoriaMetrics Cluster Monitoring POC

This project demonstrates a highly available and scalable monitoring stack using **VictoriaMetrics Cluster**. It monitors a sample environment consisting of Nginx, PostgreSQL, and RabbitMQ.

[English](#english) | [Português](#português)

---

<a name="english"></a>
## English

## Architecture Overview

The stack uses the **VictoriaMetrics Cluster** architecture, which is split into several components for maximum scalability:

- **vmstorage**: Responsible for data persistence.
- **vminsert**: Entry point for writing data (Remote Write).
- **vmselect**: Entry point for querying data (PromQL/MetricsQL).
- **vmagent**: Lightweight scraper that collects metrics from targets and sends them to `vminsert`.

### Monitored Components

- **Nginx**: Monitored via `nginx-prometheus-exporter`.
- **PostgreSQL**: Monitored via `postgres-exporter`.
- **RabbitMQ**: Monitored via its native Prometheus plugin.
- **Grafana**: Pre-configured with datasources and dashboards for all components.

## How to Run

### Prerequisites
- Docker and Docker Compose installed.

### Setup
1. Navigate to this directory:
   ```bash
   cd victoriametrics-cluster-poc
   ```
2. Start the stack:
   ```bash
   docker-compose up -d
   ```

### Accessing the Services
- **Grafana**: [http://localhost:3000](http://localhost:3000) (User: `admin` / Password: `admin`)
- **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (User: `guest` / Password: `guest`)
- **Nginx Frontend**: [http://localhost:8080](http://localhost:8080)
- **VictoriaMetrics VMUI**: [http://localhost:8481/select/0/vmui/](http://localhost:8481/select/0/vmui/)

### Important Notes
- **Scalability**: If you need more storage, you can run `docker-compose up -d --scale vmstorage=2` (although discovery flags need adjustment in production, in local Docker the cluster mode facilitates process separation).
- **Grafana**: Remember that the Prometheus URL in Grafana should now be: `http://vmselect:8481/select/0/prometheus/`.
- **Permissions**: If the "cannot read" error persists in the `vmagent` log, check if you... messed up! Wait, sorry. Check if you created the `prometheus.yml` file as root while trying to run docker with another user.

---

<a name="português"></a>
## Português

## Visão Geral da Arquitetura

Esta stack utiliza a arquitetura **VictoriaMetrics Cluster**, que é dividida em vários componentes para máxima escalabilidade:

- **vmstorage**: Responsável pela persistência dos dados.
- **vminsert**: Ponto de entrada para escrita de dados (Remote Write).
- **vmselect**: Ponto de entrada para consulta de dados (PromQL/MetricsQL).
- **vmagent**: Coletor leve (scraper) que busca métricas nos alvos e as envia para o `vminsert`.

### Componentes Monitorados

- **Nginx**: Monitorado via `nginx-prometheus-exporter`.
- **PostgreSQL**: Monitorado via `postgres-exporter`.
- **RabbitMQ**: Monitorado através do seu plugin nativo de Prometheus.
- **Grafana**: Pré-configurado com datasources e dashboards para todos os componentes.

## Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados.

### Instalação
1. Navegue até este diretório:
   ```bash
   cd victoriametrics-cluster-poc
   ```
2. Inicie a stack:
   ```bash
   docker-compose up -d
   ```

### Acessando os Serviços
- **Grafana**: [http://localhost:3000](http://localhost:3000) (Usuário: `admin` / Senha: `admin`)
- **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (Usuário: `guest` / Senha: `guest`)
- **Nginx Frontend**: [http://localhost:8080](http://localhost:8080)
- **VictoriaMetrics VMUI**: [http://localhost:8481/select/0/vmui/](http://localhost:8481/select/0/vmui/)

### Notas Importantes
- **Elasticidade**: Se tu precisar de mais storage, tu pode rodar `docker-compose up -d --scale vmstorage=2` (embora precise ajustar as flags de discovery em produção, no Docker local o modo cluster facilita a separação de processos).
- **Grafana**: Lembre-se de que a URL do Prometheus no Grafana agora deve ser: `http://vmselect:8481/select/0/prometheus/`.
- **Permissões**: Se o erro de "cannot read" persistir no log do `vmagent`, verifique se tu não fez merda! Não, calma.. Foi mal. Veja se tu não criou o arquivo `prometheus.yml` como usuário root enquanto tenta rodar o docker com outro usuário.
