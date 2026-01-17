<h1 align="center">Agencei</h1>

<p align="center">
  Controle de presença digital para eventos institucionais, simples, rápido e sem papel.
</p>

<p align="center">
  <a href="https://agencei-system.onrender.com" target="_blank">
    <img src="https://img.shields.io/badge/VISUALIZE%20O%20PROJETO%20AQUI-2962FF?style=for-the-badge&logo=render&logoColor=white" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-em%20desenvolvimento-orange" />
  <img src="https://img.shields.io/badge/projeto-acadêmico%20%2F%20pessoal-blue" />
</p>

> **Nota:** Aplicação hospedada em plano gratuito. O servidor entra em modo de espera após inatividade, portanto, o primeiro acesso pode levar até 1 minuto para carregar.

---

## Contas de Demonstração (Coringa)

Para testar as diferentes visões do sistema sem a necessidade de criar um novo cadastro, utilize as credenciais abaixo:

| Perfil | CPF | Senha | Funcionalidades |
| :--- | :--- | :--- | :--- |
| **Administrador** | `00000000001` | `admin123` | Gerenciamento de usuários, locais e logs. |
| **Organizador** | `00000000002` | `org123` | Criação de eventos e listas de presença. |
| **Aluno** | `00000000003` | `aluno123` | Inscrição em eventos e histórico pessoal. |

---

## Sobre o projeto

O **Agencei** é um sistema desenvolvido para otimizar o controle de presença em eventos e atividades institucionais, substituindo listas físicas por uma solução digital baseada em QR Code.

### O Problema
- Listas de papel ineficientes e sujeitas a rasuras.
- Lentidão no processo de entrada em grandes eventos.
- Dificuldade na consolidação posterior dos dados de presença.

### A Solução
1. O organizador realiza o cadastro do evento e define o local.
2. O sistema gera um QR Code exclusivo.
3. O participante realiza a leitura do código via dispositivo móvel.
4. A presença é validada e registrada em tempo real no banco de dados.

---

## Tecnologias Utilizadas

O projeto segue o padrão Application Factory e utiliza arquitetura MVC:

- **Backend:** Python com Flask
- **Banco de Dados:** SQLite (com SQLAlchemy ORM)
- **Autenticação:** Flask-Login
- **Frontend:** HTML5, CSS3, JavaScript e Jinja2
- **Hospedagem:** Render

---

## Instruções para Execução Local

1. Clone o repositório: `git clone https://github.com/seu-usuario/seu-repo.git`
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências: `pip install -r requirements.txt`
5. Execute o script de inicialização do banco: `python seed.py`
6. Inicie a aplicação: `python app.py`

---

## Desenvolvedor

Projeto desenvolvido por **Felipe Alves Torres**, Técnico em Informática.

<p align="center">
  <strong>Agencei</strong><br/>
  <em>Um clique — e tá marcado.</em>
</p>
