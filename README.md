# 🔍 Scanner de Rede Inteligente

Um scanner de rede avançado desenvolvido em Python que detecta dispositivos ativos e impressoras compartilhadas na rede local, com interface gráfica moderna e funcionalidades inteligentes de autenticação.

## ✨ Características

- **🚀 Scanning Rápido**: Escaneia múltiplos IPs simultaneamente usando threads
- **🖨️ Detecção de Impressoras**: Encontra impressoras de rede e compartilhadas automaticamente
- **🔐 Autenticação Inteligente**: Sistema de credenciais adaptativo que solicita login quando necessário
- **📊 Interface Moderna**: Interface gráfica responsiva com temas escuros
- **📁 Exportação CSV**: Exporta resultados para análise posterior
- **🔍 Detalhes Avançados**: Informações detalhadas sobre serviços e portas abertas
- **⚡ Instalação Automática**: Instala impressoras encontradas diretamente pelo Windows

## 🛠️ Pré-requisitos

### Software Necessário
- **Python 3.8+**
- **Nmap** - [Download aqui](https://nmap.org/download.html)
  - ⚠️ **Importante**: Durante a instalação do Nmap, marque a opção "Add Nmap to PATH"
- **Windows** (para funcionalidades WMI e impressoras compartilhadas)

### Bibliotecas Python
```bash
pip install -r requirements.txt
```

## 📦 Instalação

1. **Clone o repositório**:
```bash
git clone https://github.com/seu-usuario/network-scanner.git
cd network-scanner
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Instale o Nmap**:
   - Baixe de [nmap.org](https://nmap.org/download.html)
   - Execute o instalador
   - ✅ Marque "Add Nmap to the system PATH"

4. **Execute o scanner**:
```bash
python main.py
```

## 🚀 Como Usar

### Scanning Básico
1. Digite um IP (ex: `192.168.1.1`) ou intervalo (ex: `192.168.1.1-255`)
2. Clique em "🚀 Iniciar Scan"
3. Aguarde os resultados aparecerem

### Credenciais Automáticas
O sistema solicitará credenciais automaticamente quando:
- Encontrar dispositivos que exigem autenticação
- Detectar impressoras compartilhadas protegidas
- Acessar informações detalhadas via WMI

### Instalação de Impressoras
1. Clique com botão direito em uma impressora encontrada
2. Selecione "Instalar Impressora"
3. Siga o assistente do Windows

## 🔧 Funcionalidades Técnicas

### Métodos de Detecção
- **Nmap**: Scanning de portas e detecção de serviços
- **WMI**: Acesso a informações detalhadas do Windows
- **NET VIEW**: Listagem de compartilhamentos de rede
- **PowerShell Remoto**: Consultas avançadas quando disponível
- **Registro Remoto**: Acesso ao registro do Windows

### Portas Escaneadas
- **9100, 631, 515**: Impressoras de rede (RAW, IPP, LPD)
- **139, 445**: Compartilhamento Windows (NetBIOS, SMB)
- **80, 443**: Serviços web (HTTP, HTTPS)

### Segurança
- Credenciais criptografadas localmente
- Conexões temporárias para autenticação
- Limpeza automática de sessões

## 📊 Formatos de Saída

### CSV Export
O arquivo CSV contém:
- Categoria do dispositivo
- Endereço IP
- Hostname
- Endereço MAC
- Status/Descrição

### Detalhes do Dispositivo
- Informações de rede completas
- Lista de portas abertas
- Detalhes de impressoras compartilhadas
- Informações do fabricante

## 🔍 Exemplos de Uso

### Scan de IP Único
```
IP: 192.168.1.100
```

### Scan de Intervalo
```
IP: 192.168.1.1-254
IP: 10.0.0.1-50
```

### Scan de Subnet Específica
```
IP: 172.16.1.1-100
```

## ⚠️ Solução de Problemas

### "Nmap não encontrado"
- Reinstale o Nmap marcando "Add to PATH"
- Reinicie o terminal/programa
- Verifique: `nmap --version` no CMD

### "Erro de Credenciais"
- Verifique usuário/senha da rede
- Use formato: `DOMINIO\usuario` se aplicável
- Teste credenciais com `net use \\ip\ipc$`

### "Sem Resultados"
- Verifique conectividade de rede
- Teste ping manual: `ping 192.168.1.1`
- Confirme se o firewall permite scanning

### "Erro WMI"
- Verifique se WMI está habilitado no host remoto
- Confirme permissões administrativas
- Teste acesso manual via `wmic`

## 🤝 Contribuição

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

Desenvolvido com ❤️ para facilitar a administração de redes.

## 🔗 Links Úteis

- [Documentação do Nmap](https://nmap.org/book/)
- [WMI Reference](https://docs.microsoft.com/en-us/windows/win32/wmisdk/)
- [CustomTkinter Docs](https://customtkinter.tomschimansky.com/)

## 📈 Roadmap

- [ ] Suporte para Linux/macOS
- [ ] Interface web opcional
- [ ] Scanning de IPv6
- [ ] Detecção de vulnerabilidades
- [ ] Relatórios automatizados
- [ ] Integração com Active Directory

---

**⭐ Se este projeto te ajudou, considere dar uma estrela no GitHub!**
