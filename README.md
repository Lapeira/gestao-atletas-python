# ⚽ Sistema de Gestão de Atletas

## 📝 Sobre o Projeto
Esta é uma aplicação Full-Stack desenvolvida para facilitar a gestão interna de um clube desportivo. O sistema permite registar atletas, calcular automaticamente os seus escalões com base na data de nascimento e fazer um controlo rigoroso do pagamento de mensalidades. 
O projeto foi inicialmente construído como uma aplicação web, tendo sido posteriormente convertido numa **aplicação Desktop executável**.

## 🚀 Funcionalidades Principais
* **Gestão de Atletas:** Adicionar, listar e remover atletas da base de dados.
* **Cálculo de Escalões Automático:** O sistema calcula a idade e atribui o escalão correto (ex: Traquinas, Benjamins, Juniores, etc.).
* **Gestão Financeira:** Registo de pagamentos, verificação de meses em atraso e histórico completo de transações por atleta.
* **Autenticação Segura:** Sistema de login com passwords encriptadas e controlo de acessos (perfil Administrador vs. Utilizador normal).
* **Versão Desktop:** O sistema pode ser corrido nativamente no Windows através de uma janela dedicada, sem necessidade de abrir o browser.

## 🛠️ Tecnologias Utilizadas
* **Back-end:** Python, Flask, Flask-Login, Werkzeug (Segurança).
* **Base de Dados:** SQLite (com base de dados relacional estruturada).
* **Front-end:** HTML5, CSS3, JavaScript.
* **Desktop App:** `pywebview` e `cx_Freeze`.

## ⚙️ Como executar o projeto localmente
1. Clona este repositório.
2. Instala as dependências necessárias (Flask, etc.).
3. Para correr a versão Web: executa o ficheiro `app.py`.
4. Para correr a versão Desktop: executa o ficheiro `run.py`.
