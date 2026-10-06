"""
Coleta as informações do ambiente para a Ficha de pré-registro (seção 5).
Funciona no Windows e no Linux, usando só a biblioteca padrão do Python.

Como usar:
    python coletar_ambiente.py      (Windows)
    python3 coletar_ambiente.py     (Linux)

Gera o arquivo ambiente_windows.txt ou ambiente_linux.txt na mesma pasta.
"""

import os
import platform
import shutil
import struct
import sys
from datetime import datetime


def ler_arquivo(caminho):
    try:
        with open(caminho, encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except OSError:
        return None


# ---------------- Sistema operacional ----------------
def versao_so():
    sistema = platform.system()
    if sistema == "Windows":
        build = platform.version()  # ex.: 10.0.22631
        try:
            numero_build = int(build.split(".")[-1])
        except ValueError:
            numero_build = 0
        nome = "Windows 11" if numero_build >= 22000 else f"Windows {platform.release()}"
        edicao = platform.win32_edition() if hasattr(platform, "win32_edition") else ""
        return f"{nome} {edicao} (build {build})".replace("  ", " ")
    if sistema == "Linux":
        try:
            info = platform.freedesktop_os_release()
            nome = info.get("PRETTY_NAME", "Linux")
        except (AttributeError, OSError):
            nome = "Linux"
            texto = ler_arquivo("/etc/os-release") or ""
            for linha in texto.splitlines():
                if linha.startswith("PRETTY_NAME="):
                    nome = linha.split("=", 1)[1].strip('"')
        return f"{nome} (kernel {platform.release()})"
    return f"{sistema} {platform.release()}"


# ---------------- Processador ----------------
def nome_processador():
    sistema = platform.system()
    if sistema == "Windows":
        try:
            import winreg
            chave = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            nome, _ = winreg.QueryValueEx(chave, "ProcessorNameString")
            return nome.strip()
        except OSError:
            return platform.processor() or "não identificado"
    if sistema == "Linux":
        texto = ler_arquivo("/proc/cpuinfo") or ""
        for linha in texto.splitlines():
            if linha.lower().startswith("model name"):
                return linha.split(":", 1)[1].strip()
    return platform.processor() or "não identificado"


# ---------------- Memória RAM ----------------
def memoria_gb():
    """Retorna (total_GB, disponivel_GB)."""
    sistema = platform.system()
    if sistema == "Windows":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullTotalPhys / 1024**3, stat.ullAvailPhys / 1024**3
    if sistema == "Linux":
        valores = {}
        for linha in (ler_arquivo("/proc/meminfo") or "").splitlines():
            partes = linha.split()
            if len(partes) >= 2:
                valores[partes[0].rstrip(":")] = int(partes[1])  # em kB
        total = valores.get("MemTotal", 0) / 1024**2
        disp = valores.get("MemAvailable", 0) / 1024**2
        return total, disp
    return 0, 0


# ---------------- Máquina (detecta VM) ----------------
def modelo_maquina():
    sistema = platform.system()
    if sistema == "Windows":
        try:
            import winreg
            chave = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS"
            )
            fabricante, _ = winreg.QueryValueEx(chave, "SystemManufacturer")
            produto, _ = winreg.QueryValueEx(chave, "SystemProductName")
            return f"{fabricante} {produto}".strip()
        except OSError:
            return "não identificado"
    if sistema == "Linux":
        fabricante = ler_arquivo("/sys/class/dmi/id/sys_vendor") or ""
        produto = ler_arquivo("/sys/class/dmi/id/product_name") or ""
        return f"{fabricante} {produto}".strip() or "não identificado"
    return "não identificado"


def eh_vm(modelo):
    pistas = ["virtualbox", "vmware", "qemu", "kvm", "hyper-v", "virtual machine", "innotek"]
    return any(p in modelo.lower() for p in pistas)


# ---------------- Coleta ----------------
def main():
    total_ram, disp_ram = memoria_gb()
    disco = shutil.disk_usage(os.path.abspath(os.sep))
    modelo = modelo_maquina()
    vm = eh_vm(modelo)

    dados = [
        ("Data da coleta", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Versão do sistema", versao_so()),
        ("Arquitetura do sistema", platform.machine()),
        ("Versão do Python", platform.python_version()),
        ("Arquitetura do Python", f"{struct.calcsize('P') * 8} bits"),
        ("Processador", nome_processador()),
        ("Núcleos lógicos (vCPUs se VM)", str(os.cpu_count())),
        ("Memória RAM total (RAM atribuída se VM)", f"{total_ram:.2f} GB"),
        ("Memória disponível agora", f"{disp_ram:.2f} GB"),
        ("Armazenamento (disco do sistema)", f"{disco.total / 1024**3:.0f} GB total, "
                                             f"{disco.free / 1024**3:.0f} GB livres"),
        ("Modelo da máquina", modelo),
        ("Rodando em máquina virtual?", "Sim" if vm else "Não (provavelmente)"),
        ("Executável do Python", sys.executable),
    ]

    texto = "INFORMAÇÕES DO AMBIENTE\n" + "=" * 50 + "\n"
    for campo, valor in dados:
        texto += f"{campo:<42}: {valor}\n"

    if vm:
        texto += "\nATENÇÃO: é VM. Anote manualmente a versão do VirtualBox\n"
        texto += "e o hardware físico do computador hospedeiro.\n"

    print(texto)

    nome_arquivo = f"ambiente_{platform.system().lower()}.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"Arquivo salvo: {nome_arquivo}")


if __name__ == "__main__":
    main()
