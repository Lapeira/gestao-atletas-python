from cx_Freeze import setup, Executable

# Informações sobre a aplicação
build_exe_options = {
    "packages": ["flask", "webview"],  # Adicione outras dependências aqui
    "include_files": ["static", "templates"],  # Inclua pastas estáticas e de templates
}

# Configuração do setup
setup(
    name="Gestão de Atletas",
    version="0.1",
    description="Aplicação de Gestão de Atletas",
    options={"build_exe": build_exe_options},
    executables=[Executable("run.py", base="Win32GUI")]  # Altere base="Win32GUI" se não quiser uma janela de console no Windows
)